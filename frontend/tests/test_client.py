from typing import Any

import pytest
import requests

from frontend.api import client
from frontend.core.settings import API_URL


def _raise(exc: Exception):
    def fake(*args: Any, **kwargs: Any):
        raise exc

    return fake


def _analyze() -> dict[str, Any]:
    return client.analyze_conversation(b"RIFF....", "call.wav", translate=False, content_type="audio/wav")


@pytest.mark.parametrize(("translate", "form_value"), [(True, "true"), (False, "false")])
def test_success_returns_body_and_sends_multipart(monkeypatch, make_response, english_result, translate, form_value):
    calls: list[dict[str, Any]] = []

    def fake_post(url: str, **kwargs: Any) -> requests.Response:
        calls.append({"url": url, **kwargs})
        return make_response(200, english_result)

    monkeypatch.setattr(requests, "post", fake_post)
    result = client.analyze_conversation(b"RIFF....", "call.wav", translate=translate, content_type="audio/wav")

    assert result == english_result
    (call,) = calls
    assert call["url"] == f"{API_URL}/v1/conversation"
    assert call["files"] == {"audio": ("call.wav", b"RIFF....", "audio/wav")}
    assert call["data"] == {"translate": form_value}
    assert call["timeout"] == 3600


def test_connection_error(monkeypatch):
    monkeypatch.setattr(requests, "post", _raise(requests.ConnectionError("Connection refused")))
    result = _analyze()
    assert result["error"] == "Connection Error"
    assert API_URL in result["message"]
    assert result["technical_details"] == "Connection refused"


@pytest.mark.parametrize("exc", [requests.ReadTimeout("read timed out"), requests.ConnectTimeout("connect timed out")])
def test_timeout(monkeypatch, exc):
    monkeypatch.setattr(requests, "post", _raise(exc))
    result = _analyze()
    assert result["error"] == "Timeout"
    assert result["technical_details"] == str(exc)


@pytest.mark.parametrize(
    ("status", "detail", "title"),
    [
        (422, "Could not decode audio: invalid data", "Invalid Audio"),
        (503, "Models are loading; check GET /health", "Models Not Ready"),
        (413, "Upload exceeds 100 MB", "File Too Large"),
    ],
)
def test_http_error_uses_json_detail(monkeypatch, make_response, status, detail, title):
    monkeypatch.setattr(requests, "post", lambda url, **kw: make_response(status, {"detail": detail}))
    assert _analyze() == {"error": title, "message": detail}


def test_http_error_without_json_body(monkeypatch, make_response):
    monkeypatch.setattr(requests, "post", lambda url, **kw: make_response(502, text="Bad Gateway"))
    result = _analyze()
    assert result["error"] == "HTTP Error"
    assert "502" in result["message"]
    assert result["technical_details"] == "Bad Gateway"


def test_non_json_success_is_an_error(monkeypatch, make_response):
    monkeypatch.setattr(requests, "post", lambda url, **kw: make_response(200, text="<html>proxy</html>"))
    assert _analyze()["error"] == "Invalid Response"


def test_health(monkeypatch, make_response):
    payload = {"status": "ready", "translation_available": True}
    monkeypatch.setattr(requests, "get", lambda url, **kw: make_response(200, payload))
    assert client.get_health() == payload


def test_health_unreachable(monkeypatch):
    monkeypatch.setattr(requests, "get", _raise(requests.ConnectionError("refused")))
    assert client.get_health()["error"] == "Connection Error"
