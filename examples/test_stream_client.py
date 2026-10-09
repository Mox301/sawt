"""The streaming client against a scripted local WebSocket server (no models, no audio files)."""

import asyncio
import json

import pytest
import stream_client
import websockets

CHUNKS = [b"chunk-1", b"chunk-2"]
STARTED = {"type": "started", "session_id": "s1"}
ACK = {"type": "chunk_ack", "chunk_number": 1, "total_duration_s": 5.0}


def run(replies: list[dict], monkeypatch: pytest.MonkeyPatch) -> tuple[list, dict]:
    """Stream to a server that answers each client message with the next reply, then closes."""
    monkeypatch.setattr(stream_client, "segments", lambda path, seconds: CHUNKS)
    received = []

    async def handler(ws: websockets.ServerConnection) -> None:
        for reply in replies:
            if reply["type"] != "result":  # the result follows "processing" with no client message
                received.append(await ws.recv())
            await ws.send(json.dumps(reply))

    async def main() -> dict:
        async with websockets.serve(handler, "127.0.0.1", 0) as server:
            port = server.sockets[0].getsockname()[1]
            return await stream_client.stream(f"ws://127.0.0.1:{port}", "/some/local/dir/call.wav", False, 5.0)

    return received, asyncio.run(main())


def test_streams_and_returns_result_sending_only_the_file_name(monkeypatch):
    processing = {"type": "processing", "total_duration_s": 10.0}
    received, result = run([STARTED, ACK, ACK, processing, {"type": "result", "data": {"a": 1}}], monkeypatch)
    assert json.loads(received[0])["filename"] == "call.wav"
    assert received[1:3] == CHUNKS
    assert result == {"a": 1}


@pytest.mark.parametrize(
    ("replies", "message"),
    [
        ([{"type": "error", "status": 503, "detail": "loading"}], "error 503: loading"),
        ([STARTED, {"type": "error", "status": 413, "detail": "too long"}], "error 413: too long"),
        ([STARTED, ACK, ACK, {"type": "error", "status": 422, "detail": "empty"}], "error 422: empty"),
    ],
)
def test_server_error_exits_with_status_and_detail(replies, message, monkeypatch):
    with pytest.raises(SystemExit, match=message):
        run(replies, monkeypatch)
