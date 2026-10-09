import asyncio
import json
import sys

from fastapi.testclient import TestClient

from backend.infrastructure.ml.registry import ModelRegistry
from backend.main import create_app
from backend.tests.conftest import tone, wav_bytes
from backend.tests.fakes import FakeAudioLLM


def test_health_reports_models(client):
    body = client.get("/api/v1/health").json()
    assert body["status"] == "ready"
    assert body["models"]["audio_llm"]["state"] == "ready"
    assert body["translation_available"] is True and body["diarization_available"] is True


def test_conversation(client, dialogue_wav):
    response = client.post("/api/v1/conversations/analyze", files={"audio": ("call.wav", dialogue_wav, "audio/wav")})
    assert response.status_code == 200, response.text
    body = response.json()

    assert set(body) == {"analysis", "diarization_info", "acoustic_features", "metadata", "turn_taking_metrics"}
    assert body["diarization_info"]["num_speakers"] == 2
    assert body["metadata"]["audio_filename"] == "call.wav"
    assert body["metadata"]["processing_timestamp"]
    assert body["analysis"]["conversation_analysis"]["duration_estimate"].endswith("seconds")
    assert body["analysis"]["prosody_analysis"]["quantitative_metrics"]["voice_quality"]["spectral_centroid_hz"] > 0


def test_conversation_prompt_includes_diarization_context(make_client, dialogue_wav):
    llm = FakeAudioLLM()
    client = make_client(audio_llm=llm)
    client.post("/api/v1/conversations/analyze", files={"audio": ("call.wav", dialogue_wav)})
    assert "Speaker diarization detected 2 speakers" in llm.calls[0][1]


def test_conversation_translated(client, dialogue_wav):
    body = client.post(
        "/api/v1/conversations/analyze", files={"audio": ("call.wav", dialogue_wav)}, data={"translate": "true"}
    ).json()
    assert set(body) == {"EN", "AR"}
    assert body["AR"]["analysis"]["conversation_analysis"]["overall_sentiment"] == "مختلط"


def test_translate_without_model_is_flagged(make_client, dialogue_wav):
    client = make_client()  # no text model
    assert client.get("/api/v1/health").json()["status"] == "degraded"
    body = client.post(
        "/api/v1/conversations/analyze", files={"audio": ("a.wav", dialogue_wav)}, data={"translate": "true"}
    ).json()
    assert body["metadata"]["translation"] == "unavailable"


def test_errors(make_client, client, dialogue_wav):
    assert client.post("/api/v1/conversations/analyze", files={"audio": ("a.wav", b"garbage")}).status_code == 422
    too_big = dialogue_wav + b"\0" * (1024 * 1024)
    assert client.post("/api/v1/conversations/analyze", files={"audio": ("a.wav", too_big)}).status_code == 413
    # Within the multipart allowance of the body limit, so the route's own per-file check rejects it.
    just_over = b"\0" * (1024 * 1024 + 1)
    assert client.post("/api/v1/conversations/analyze", files={"audio": ("a.wav", just_over)}).status_code == 413

    broken = make_client(fail_audio=True)
    assert broken.get("/api/v1/health").json()["status"] == "unavailable"
    assert broken.post("/api/v1/conversations/analyze", files={"audio": ("a.wav", dialogue_wav)}).status_code == 503


def test_root_points_to_docs_and_health(client):
    assert client.get("/").json()["health"] == "/api/v1/health"


def test_audio_longer_than_the_limit_is_rejected(settings, make_client):
    settings.max_audio_minutes, settings.max_upload_mb = 1, 10
    client = make_client()
    response = client.post("/api/v1/conversations/analyze", files={"audio": ("a.wav", wav_bytes(tone(200, 61)))})
    assert response.status_code == 413
    assert response.json() == {"detail": "Audio longer than 1 minutes"}


def test_declared_body_over_the_limit_is_rejected_before_reading(client):
    response = client.post(
        "/api/v1/conversations/analyze",
        content=b"tiny",
        headers={"content-type": "multipart/form-data; boundary=B", "content-length": str(2 * 1024 * 1024)},
    )
    assert response.status_code == 413
    assert response.json() == {"detail": "Upload exceeds 1 MB"}


def test_streamed_body_stops_at_the_limit(client):
    """A chunked upload has no Content-Length: the body is counted as it arrives."""
    head = b'--B\r\nContent-Disposition: form-data; name="audio"; filename="a.wav"\r\n\r\n'
    chunks = [head] + [b"\0" * 64 * 1024] * 40  # 2.5 MB against a 1 MB limit
    pulled, sent = 0, []

    async def receive():
        nonlocal pulled
        pulled += 1
        return {"type": "http.request", "body": chunks[pulled - 1], "more_body": pulled < len(chunks)}

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/v1/conversations/analyze",
        "raw_path": b"/api/v1/conversations/analyze",
        "root_path": "",
        "query_string": b"",
        "headers": [(b"content-type", b"multipart/form-data; boundary=B")],
        "client": ("test", 1),
        "server": ("test", 80),
    }
    asyncio.run(client.app(scope, receive, send))

    assert sent[0]["status"] == 413
    assert json.loads(sent[1]["body"]) == {"detail": "Upload exceeds 1 MB"}
    assert pulled < len(chunks)


def test_health_reports_unavailable_when_torch_is_missing(settings, monkeypatch):
    monkeypatch.setitem(sys.modules, "torch", None)
    monkeypatch.delitem(sys.modules, "backend.infrastructure.ml.device", raising=False)
    with TestClient(create_app(settings, ModelRegistry(settings), load_in_background=False)) as client:
        body = client.get("/api/v1/health").json()
    assert body["status"] == "unavailable"
    assert body["models"]["audio_llm"]["state"] == "failed"
    assert "torch" in body["models"]["audio_llm"]["error"]
