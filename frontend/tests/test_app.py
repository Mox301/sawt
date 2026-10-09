"""Smoke tests: run the real Streamlit script headlessly with the HTTP layer faked."""

import json
import threading
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


def test_arabic_view_hides_translated_placeholders(monkeypatch, make_response, placeholder_response):
    at = _app(monkeypatch, make_response)
    at.session_state["result"] = placeholder_response
    at.run()

    assert not at.exception
    page = "\n".join(_text(elements) for elements in (at.markdown, at.info, at.warning))
    for placeholder in ("غير معروف", "غير موصوف", "غير محدد", "لم يتم تقديم تحليل مفصل."):
        assert placeholder not in page
    assert t("detailed_report", "AR") not in page
    assert t("dominance_pattern", "AR") not in page
    assert t("speaker_analysis", "AR") in page


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


def test_pending_analysis_survives_a_language_switch(monkeypatch, make_response, bilingual_response):
    release, posts = threading.Event(), []

    def slow_post(url: str, **kwargs: Any) -> requests.Response:
        posts.append(url)
        release.wait(timeout=10)
        return make_response(200, bilingual_response)

    monkeypatch.setattr(requests, "post", slow_post)
    at = _app(monkeypatch, make_response)
    at.run()
    at.file_uploader(key="audio").set_value(("call.wav", b"RIFF", "audio/wav")).run()
    try:
        at.button(key="analyze").click().run()
        assert at.button(key="analyze").disabled
        # A daemon thread, so stopping the UI does not wait for the request.
        workers = [thread for thread in threading.enumerate() if thread.name == "sawt-analysis"]
        assert workers and all(thread.daemon for thread in workers)
        at.radio(key="lang").set_value("EN").run()

        assert not at.exception
        assert at.button(key="analyze").disabled
        (status,) = at.status
        assert status.state == "running"
        assert status.label.startswith(t("analyzing", "EN"))
    finally:
        release.set()

    at.session_state["job"].future.result(timeout=10)
    at.run()

    assert not at.exception
    assert len(posts) == 1
    assert not at.status
    assert t("success", "EN").split("{}")[0] in _text(at.success)
    assert at.session_state["result"] == bilingual_response
    assert at.session_state["file_name"] == "call.wav"
    assert not at.button(key="analyze").disabled


def test_a_failing_job_ends_with_an_error(monkeypatch, make_response):
    release = threading.Event()

    def broken_post(url: str, **kwargs: Any) -> requests.Response:
        release.wait(timeout=10)
        raise RuntimeError("boom")

    monkeypatch.setattr(requests, "post", broken_post)
    at = _app(monkeypatch, make_response)
    at.session_state["lang"] = "EN"
    at.run()
    at.file_uploader(key="audio").set_value(("call.wav", b"RIFF", "audio/wav")).run()
    at.button(key="analyze").click().run()
    job = at.session_state["job"]
    release.set()
    job.future.exception(timeout=10)
    at.run()

    assert not at.exception
    assert at.session_state["job"] is None
    assert t("error", "EN").format("boom") in _text(at.error)
    assert not at.button(key="analyze").disabled


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


@pytest.mark.parametrize("lang", ["AR", "EN"])
def test_renders_real_pipeline_output(monkeypatch, make_response, lang):
    """A response recorded from the real pipeline (Voxtral + pyannote + Ollama Qwen3) on a synthetic clip."""
    fixture = Path(__file__).parent / "fixtures" / "real_bilingual_response.json"
    at = _app(monkeypatch, make_response)
    at.session_state["lang"] = lang
    at.session_state["result"] = json.loads(fixture.read_text())
    at.session_state["file_name"] = "en_dialog.wav"
    at.run()

    assert not at.exception
    page = "\n".join(_text(elements) for elements in (at.markdown, at.info, at.warning))
    for key in ("conv_overview", "speaker_timeline", "speaker_analysis", "prosody_analysis", "interaction_dynamics"):
        assert t(key, lang) in page
    assert ("سلبي" if lang == "AR" else "Negative") in [m.value for m in at.metric]
    assert "__SPK" not in page
