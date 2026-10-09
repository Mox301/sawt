"""Smoke tests: run the real Streamlit script headlessly with the HTTP layer faked."""

from pathlib import Path
from typing import Any

import pytest
import requests
import streamlit as st
from streamlit.testing.v1 import AppTest

from frontend.core.i18n import t
from frontend.core.settings import API_URL
from frontend.core.state import Outcome

APP_PATH = str(Path(__file__).resolve().parents[1] / "app.py")

READY = {
    "status": "ready",
    "version": "1.0.0",
    "device": "cpu",
    "models": {},
    "translation_available": True,
    "diarization_available": True,
}


@pytest.fixture(autouse=True)
def _clear_health_cache():
    st.cache_data.clear()
    yield
    st.cache_data.clear()


def _app(monkeypatch, make_response, health: dict[str, Any] = READY) -> AppTest:
    monkeypatch.setattr(requests, "get", lambda url, **kw: make_response(200, health))
    return AppTest.from_file(APP_PATH, default_timeout=30)


def _text(elements) -> str:
    return "\n".join(str(e.value) for e in elements)


def test_renders_in_both_languages(monkeypatch, make_response):
    at = _app(monkeypatch, make_response)
    at.run()
    assert not at.exception
    assert "Sawt" in at.title[0].value
    assert at.radio(key="lang").value == "AR"
    assert t("subtitle", "AR") in _text(at.markdown)

    at.radio(key="lang").set_value("EN").run()
    assert not at.exception
    assert "Sawt" in at.title[0].value
    assert t("subtitle", "EN") in _text(at.markdown)


@pytest.mark.parametrize("lang", ["AR", "EN"])
def test_renders_bilingual_results(monkeypatch, make_response, bilingual_response, lang):
    at = _app(monkeypatch, make_response)
    at.session_state["lang"] = lang
    at.session_state["result"] = bilingual_response
    at.session_state["file_name"] = "call.wav"
    at.run()

    assert not at.exception
    markdown = _text(at.markdown)
    for key in ("conv_overview", "speaker_timeline", "speaker_analysis", "prosody_analysis", "interaction_dynamics"):
        assert t(key, lang) in markdown
    assert t("english_only", lang) not in _text(at.info)
    expected_sentiment = "مختلط" if lang == "AR" else "Mixed"
    assert expected_sentiment in [m.value for m in at.metric]


def test_english_only_result_in_arabic_ui(monkeypatch, make_response, untranslated_response):
    at = _app(monkeypatch, make_response, {**READY, "translation_available": False})
    at.session_state["result"] = untranslated_response
    at.run()

    assert not at.exception
    assert t("english_only", "AR") in _text(at.info)
    assert t("conv_overview", "AR") in _text(at.markdown)
    assert "Mixed" in [m.value for m in at.metric]


def test_outcome_messages_survive_the_rerun(monkeypatch, make_response):
    at = _app(monkeypatch, make_response)
    at.session_state["lang"] = "EN"
    at.session_state["outcome"] = Outcome(12.5)
    at.run()
    assert t("success", "EN").format("12.5 seconds") in _text(at.success)

    error = {"error": "Invalid Audio", "message": "Could not decode audio", "technical_details": "HTTP 422"}
    at.session_state["outcome"] = Outcome(0.3, error)
    at.run()
    assert not at.exception
    (message,) = [e.value for e in at.error]
    assert message.startswith(t("error", "EN").format("Could not decode audio"))
    assert "Technical details: HTTP 422" in message


def test_models_loading_notice(monkeypatch, make_response):
    at = _app(monkeypatch, make_response, {**READY, "status": "loading"})
    at.run()
    assert not at.exception
    assert t("models_loading", "AR") in _text(at.info)


def test_api_unreachable_notice(monkeypatch):
    def refuse(*args: Any, **kwargs: Any):
        raise requests.ConnectionError("refused")

    monkeypatch.setattr(requests, "get", refuse)
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception
    assert t("api_unreachable", "AR").format(API_URL) in _text(at.warning)
