"""Speaker sections: diarization timeline and statistics, and per-speaker analysis cards."""

from typing import Any

import streamlit as st

from frontend.components.charts import speaker_timeline_figure, speaking_time_figure
from frontend.core.i18n import Lang, t
from frontend.utils.formatting import format_speaker_label, format_time


def render_speaker_timeline(diarization: dict[str, Any], lang: Lang) -> None:
    if "speakers" not in diarization:
        return

    st.markdown(f"### {t('speaker_timeline', lang)}")
    st.caption(t("timeline_caption", lang))
    if timeline := speaker_timeline_figure(diarization, lang):
        st.plotly_chart(timeline)

    st.markdown(f"#### {t('speaker_stats', lang)}")
    chart_col, stats_col = st.columns(2)
    with chart_col:
        if pie := speaking_time_figure(diarization, lang):
            st.plotly_chart(pie)
    with stats_col:
        for speaker, stat in diarization.get("statistics", {}).items():
            st.markdown(f"**{format_speaker_label(speaker, lang)}**")
            col1, col2, col3 = st.columns(3)
            col1.metric(t("time", lang), format_time(stat.get("total_speaking_time", 0), lang))
            col2.metric(t("turns", lang), stat.get("num_turns", 0))
            col3.metric(t("avg_turn", lang), format_time(stat.get("average_turn_duration", 0), lang))

    st.divider()


def render_speakers(speakers: list[dict[str, Any]], lang: Lang) -> None:
    st.markdown(f"### {t('speaker_analysis', lang)}")
    for speaker in speakers:
        label = format_speaker_label(speaker.get("speaker_id", "Unknown Speaker"), lang)
        with st.expander(label, expanded=True):
            _render_speaker_card(speaker, lang)


def _render_speaker_card(speaker: dict[str, Any], lang: Lang) -> None:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(t("sentiment", lang), speaker.get("sentiment", "Unknown"))
        st.caption(t("sentiment_caption", lang))
    with col2:
        st.metric(t("role", lang), speaker.get("role", "Unknown"))
        st.caption(t("role_caption", lang))
    with col3:
        st.metric(t("speaking_time", lang), speaker.get("speaking_time_percentage", "Unknown"))
        st.caption(t("speaking_time_caption", lang))

    style = speaker.get("speaking_style", "")
    if style and style != "Not described":
        st.markdown(f"**{t('style', lang)}:** {style}")

    emotional_state = speaker.get("emotional_state", "")
    if emotional_state and emotional_state != "Not described":
        st.markdown(f"**{t('emotional_state', lang)}:** {emotional_state}")

    contributions = speaker.get("key_contributions", "")
    if contributions and contributions != "Not specified":
        st.markdown(f"**{t('key_contributions', lang)}:**")
        st.markdown(contributions)

    if phrases := speaker.get("characteristic_phrases", []):
        st.markdown(f"**{t('characteristic_phrases', lang)}:**")
        for phrase in phrases:
            st.markdown(f"- {phrase}")
