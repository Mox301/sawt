"""Sawt web UI.

Run from the repository root:  PYTHONPATH=. streamlit run frontend/app.py
"""

import time
from typing import Any

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from frontend.api import client
from frontend.components.dynamics import render_dynamics
from frontend.components.export import render_export
from frontend.components.overview import render_detailed_analysis, render_overview
from frontend.components.prosody import render_prosody
from frontend.components.speakers import render_speaker_timeline, render_speakers
from frontend.core import state
from frontend.core.i18n import LANGUAGE_LABEL, LANGUAGE_NAMES, LANGUAGES, Lang, t
from frontend.core.settings import API_URL, AUDIO_TYPES, HEALTH_CACHE_TTL_S, PAGE_CONFIG, REPO_URL
from frontend.services.result_parser import is_bilingual, parse_result
from frontend.utils.formatting import format_time
from frontend.utils.styles import apply_styles


@st.cache_data(ttl=HEALTH_CACHE_TTL_S, show_spinner=False)
def fetch_health() -> dict[str, Any]:
    return client.get_health()


def render_header(lang: Lang) -> None:
    st.title(t("title", lang))
    st.markdown(t("subtitle", lang))
    st.divider()
    with st.expander(t("about_expander", lang)):
        st.markdown(t("about_content", lang))
    st.divider()


def render_health_notice(health: dict[str, Any], lang: Lang) -> None:
    if "error" in health:
        st.warning(t("api_unreachable", lang).format(API_URL))
    elif health.get("status") == "loading":
        st.info(t("models_loading", lang))
    elif health.get("status") == "unavailable":
        st.error(t("models_unavailable", lang))


def render_analysis(uploaded: UploadedFile, translate: bool, lang: Lang) -> None:
    st.audio(uploaded, format=uploaded.type or "audio/wav")
    if st.button(t("analyze_btn", lang), type="primary", use_container_width=True, disabled=state.is_analyzing()):
        state.start_analysis()
        st.rerun()

    if state.is_analyzing():
        with st.spinner(t("analyzing", lang)):
            started = time.perf_counter()
            response = client.analyze_conversation(
                uploaded.getvalue(), uploaded.name, translate=translate, content_type=uploaded.type
            )
        state.finish_analysis(response, uploaded.name, time.perf_counter() - started)
        st.rerun()


def render_outcome(lang: Lang) -> None:
    outcome = state.pop_outcome()
    if outcome is None:
        return
    if outcome.error is None:
        st.success(t("success", lang).format(format_time(outcome.elapsed_s, lang)))
        return
    message = outcome.error.get("message", outcome.error["error"])
    if details := outcome.error.get("technical_details"):
        message = f"{message}\n\n{t('technical_details', lang)}: {details}"
    st.error(t("error", lang).format(message))


def render_results(data: dict[str, Any], lang: Lang) -> None:
    view = parse_result(data, lang)
    st.divider()
    if lang == "AR" and not is_bilingual(data):
        st.info(t("english_only", lang))

    if view.conversation:
        render_overview(view.conversation, lang, view.duration_s)
        st.divider()
    render_speaker_timeline(view.diarization, lang)
    if view.speakers:
        render_speakers(view.speakers, lang)
        st.divider()
    if view.prosody:
        render_prosody(view.prosody, lang)
        st.divider()
    if view.interaction and view.num_speakers > 1:
        render_dynamics(view.interaction, lang)
        st.divider()
    if view.detailed_analysis:
        render_detailed_analysis(view.detailed_analysis, lang)
        st.divider()
    render_export(data, state.file_name(), lang)


def render_footer() -> None:
    st.divider()
    st.markdown(
        f"<div style='text-align: center; color: gray; font-size: 0.9em;'>"
        f"Sawt · <a href='https://{REPO_URL}'>{REPO_URL}</a></div>",
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(**PAGE_CONFIG)
    state.init()

    lang: Lang = st.radio(
        LANGUAGE_LABEL, LANGUAGES, format_func=LANGUAGE_NAMES.__getitem__, horizontal=True, key="lang"
    )
    apply_styles(lang)
    render_header(lang)

    health = fetch_health()
    render_health_notice(health, lang)

    # A fixed key keeps the uploaded file when the (translated) label changes.
    uploaded = st.file_uploader(t("upload_label", lang), type=AUDIO_TYPES, help=t("upload_help", lang), key="audio")
    if uploaded is not None:
        render_analysis(uploaded, translate=bool(health.get("translation_available")), lang=lang)
    render_outcome(lang)

    if (data := state.result()) is not None:
        render_results(data, lang)
    render_footer()


main()
