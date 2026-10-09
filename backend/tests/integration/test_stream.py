import asyncio

import pytest
from starlette.websockets import WebSocketDisconnect

from backend.services.streaming import StreamSession
from backend.tests.conftest import tone, wav_bytes


def _chunks():
    return [wav_bytes(tone(140, 1.0)), wav_bytes(tone(240, 0.8)), wav_bytes(tone(140, 0.9))]


def test_stream_conversation(client):
    with client.websocket_connect("/api/v1/conversations/stream") as ws:
        ws.send_json({"type": "start", "translate": False, "filename": "live.wav"})
        assert ws.receive_json()["type"] == "started"
        for i, chunk in enumerate(_chunks(), start=1):
            ws.send_bytes(chunk)
            assert ws.receive_json()["chunk_number"] == i
        ws.send_json({"type": "end"})
        assert ws.receive_json() == {"type": "processing", "total_duration_s": 2.7}
        result = ws.receive_json()
    assert result["type"] == "result"
    assert result["data"]["metadata"]["audio_filename"] == "live.wav"
    assert result["data"]["diarization_info"]["num_speakers"] == 2


def test_stream_with_translation(client):
    with client.websocket_connect("/api/v1/conversations/stream") as ws:
        ws.send_json({"type": "start", "translate": True})
        ws.receive_json()
        ws.send_bytes(_chunks()[0])
        ws.receive_json()
        ws.send_json({"type": "end"})
        ws.receive_json()
        data = ws.receive_json()["data"]
    assert set(data) == {"EN", "AR"}
    assert data["AR"]["analysis"]["conversation_analysis"]["overall_sentiment"] == "مختلط"


def test_stream_chunks_are_decoded_off_the_event_loop(client, monkeypatch):
    on_event_loop = []
    add_chunk = StreamSession.add_chunk

    def spy(self, data):
        try:
            asyncio.get_running_loop()
            on_event_loop.append(True)
        except RuntimeError:
            on_event_loop.append(False)
        return add_chunk(self, data)

    monkeypatch.setattr(StreamSession, "add_chunk", spy)
    with client.websocket_connect("/api/v1/conversations/stream") as ws:
        ws.send_json({"type": "start"})
        ws.receive_json()
        ws.send_bytes(_chunks()[0])
        assert ws.receive_json()["type"] == "chunk_ack"
    assert on_event_loop == [False]


def test_stream_rejects_bad_protocol(client):
    with client.websocket_connect("/api/v1/conversations/stream") as ws:
        ws.send_json({"type": "chunk"})
        error = ws.receive_json()
        assert error["type"] == "error" and error["status"] == 400
        with pytest.raises(WebSocketDisconnect):
            ws.receive_json()


def test_stream_end_without_audio(client):
    with client.websocket_connect("/api/v1/conversations/stream") as ws:
        ws.send_json({"type": "start"})
        ws.receive_json()
        ws.send_json({"type": "end"})
        assert ws.receive_json() == {"type": "error", "status": 422, "detail": "No audio received"}
