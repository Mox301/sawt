"""WebSocket streaming: send audio in chunks, receive the analysis when done.

Protocol (see docs/api.md):
  client → {"type": "start", "mode": "conversation"|"sentiment", "translate": bool}
  server → {"type": "started", "session_id": ...}
  client → binary frames, each an independently decodable audio segment
  server → {"type": "chunk_ack", "chunk_number": n, "total_duration_s": s}   (per frame)
  client → {"type": "end"}
  server → {"type": "processing"} then {"type": "result", "data": {...}} and closes
Any failure → {"type": "error", "detail": ...} and the socket closes.
"""

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from backend.api.errors import status_code_for
from backend.api.schemas import StreamEnd, StreamStart
from backend.container import Container
from backend.core.exceptions import ModelNotReadyError, SawtError, StreamProtocolError
from backend.infrastructure.audio_io import prepared_audio
from backend.services.streaming import StreamSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1", tags=["streaming"])


@router.websocket("/stream")
async def stream(websocket: WebSocket) -> None:
    container: Container = websocket.app.state.container
    await websocket.accept()
    try:
        if not container.ready:
            raise ModelNotReadyError("Models are not ready; check GET /health")
        with container.sessions.slot():
            await _run_session(websocket, container)
    except WebSocketDisconnect:
        logger.info("Stream client disconnected")
    except SawtError as e:
        await _send_error(websocket, e)
    except Exception as e:
        logger.exception("Stream failed")
        await _send_error(websocket, e)


async def _run_session(websocket: WebSocket, container: Container) -> None:
    settings = container.settings
    timeout = settings.stream_idle_timeout_s

    start = _parse(await _receive(websocket, timeout), StreamStart)
    session = StreamSession(start.mode, start.translate, settings.max_upload_bytes)
    await websocket.send_json({"type": "started", "session_id": session.session_id, "mode": session.mode})

    while True:
        message = await _receive(websocket, timeout)
        if message.get("bytes") is not None:
            ack = session.add_chunk(message["bytes"])
            await websocket.send_json({"type": "chunk_ack", **ack})
        elif message.get("text") is not None:
            _parse(message, StreamEnd)
            break

    audio = session.finish()
    await websocket.send_json({"type": "processing", "total_duration_s": round(session.duration_s, 3)})

    def run():
        with prepared_audio(audio) as prepared:
            if session.mode == "sentiment":
                return container.sentiment.analyze(prepared, session.translate)
            return container.conversation.analyze(prepared, start.filename, session.translate)

    result = await container.gate.run(run)
    await websocket.send_json({"type": "result", "session_id": session.session_id, "data": result})
    await websocket.close()


async def _receive(websocket: WebSocket, timeout: float) -> dict:
    try:
        message = await asyncio.wait_for(websocket.receive(), timeout=timeout)
    except TimeoutError:
        raise StreamProtocolError(f"No message for {timeout}s; closing idle session") from None
    if message["type"] == "websocket.disconnect":
        raise WebSocketDisconnect(message.get("code", 1000))
    return message


def _parse(message: dict, model):
    try:
        return model.model_validate(json.loads(message.get("text") or ""))
    except (json.JSONDecodeError, ValidationError) as e:
        raise StreamProtocolError(f"Expected a {model.__name__} message: {e}") from e


async def _send_error(websocket: WebSocket, error: Exception) -> None:
    code = status_code_for(error) if isinstance(error, SawtError) else 500
    try:
        await websocket.send_json({"type": "error", "status": code, "detail": str(error)})
        await websocket.close(code=1011 if code >= 500 else 1008)
    except Exception:
        pass  # client already gone
