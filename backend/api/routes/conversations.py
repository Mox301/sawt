"""Conversation analysis: upload a recording, or stream it over a WebSocket."""

import asyncio
import json
import logging

from fastapi import APIRouter, Depends, File, Form, UploadFile, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from backend.api.dependencies import require_ready
from backend.api.errors import status_code_for
from backend.api.schemas import AnalysisResponse, ErrorResponse, StreamEnd, StreamStart
from backend.container import Container
from backend.core.exceptions import ModelNotReadyError, PayloadTooLargeError, SawtError, StreamProtocolError
from backend.infrastructure.audio_io import decode, prepared_audio
from backend.services.streaming import StreamSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])

ERRORS = {
    413: {"model": ErrorResponse, "description": "Upload exceeds SAWT_MAX_UPLOAD_MB or SAWT_MAX_AUDIO_MINUTES"},
    422: {"model": ErrorResponse, "description": "File could not be decoded as audio"},
    503: {"model": ErrorResponse, "description": "Models are still loading"},
}


@router.post("/analyze", response_model=AnalysisResponse, responses=ERRORS)
async def analyze(
    audio: UploadFile = File(..., description="Audio file (wav, mp3, m4a, flac, ogg …)"),
    translate: bool = Form(False, description="Also return an Arabic version: {EN, AR}"),
    container: Container = Depends(require_ready),
) -> AnalysisResponse:
    """Multi-speaker conversation analysis: diarization, prosody, turn-taking and the
    audio-LLM's conversation, speaker and interaction analysis."""
    max_bytes = container.settings.max_upload_bytes
    data = await audio.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise PayloadTooLargeError(f"Upload exceeds {max_bytes // (1024 * 1024)} MB")
    filename = audio.filename or "upload"

    def run():
        with prepared_audio(decode(data, container.settings.max_audio_seconds)) as prepared:
            return container.conversation.analyze(prepared, filename, translate)

    return await container.gate.run(run)


@router.websocket("/stream")
async def stream(websocket: WebSocket) -> None:
    """Send audio in chunks and receive the analysis when the stream ends.

    Protocol (see docs/api.md):
      client → {"type": "start", "translate": bool, "filename": str}
      server → {"type": "started", "session_id": ...}
      client → binary frames, each an independently decodable audio segment
      server → {"type": "chunk_ack", "chunk_number": n, "total_duration_s": s}   (per frame)
      client → {"type": "end"}
      server → {"type": "processing"} then {"type": "result", "data": {...}} and closes
    Any failure → {"type": "error", "status": ..., "detail": ...} and the socket closes.
    """
    container: Container = websocket.app.state.container
    await websocket.accept()
    try:
        if not container.ready:
            raise ModelNotReadyError("Models are not ready; check GET /api/v1/health")
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
    session = StreamSession(start.translate, settings.max_upload_bytes, settings.max_audio_seconds)
    await websocket.send_json({"type": "started", "session_id": session.session_id})

    while True:
        message = await _receive(websocket, timeout)
        if message.get("bytes") is not None:
            # Decoding runs FFmpeg; keep it off the event loop.
            ack = await run_in_threadpool(session.add_chunk, message["bytes"])
            await websocket.send_json({"type": "chunk_ack", **ack})
        elif message.get("text") is not None:
            _parse(message, StreamEnd)
            break

    audio = session.finish()
    await websocket.send_json({"type": "processing", "total_duration_s": round(session.duration_s, 3)})

    def run():
        with prepared_audio(audio) as prepared:
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
