"""Prosody and acoustic analysis section."""

from typing import Any

import streamlit as st

from frontend.core.i18n import Lang, t

_MARKERS = (("emphasis_usage", "emphasis"), ("pause_patterns", "pauses"), ("intonation_variety", "intonation"))


def render_prosody(prosody: dict[str, Any], lang: Lang) -> None:
    st.markdown(f"### {t('prosody_analysis', lang)}")
    st.caption(t("prosody_caption", lang))

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t("pitch", lang), prosody.get("overall_pitch", "Unknown"))
    col2.metric(t("speaking_rate", lang), prosody.get("overall_speaking_rate", "Unknown"))
    col3.metric(t("energy", lang), prosody.get("overall_energy", "Unknown"))
    col4.metric(t("tone_quality", lang), prosody.get("tone_quality", "Not described"))

    if progression := prosody.get("emotional_progression", ""):
        st.info(f"**{t('emotional_progression', lang)}:** {progression}")

    col1, col2 = st.columns(2)
    with col1:
        if features := prosody.get("notable_acoustic_features", []):
            st.markdown(f"**{t('notable_features', lang)}:**")
            for feature in features:
                st.markdown(f"• {feature}")
        if differences := prosody.get("speaker_prosody_differences", ""):
            st.markdown(f"**{t('speaker_differences', lang)}:**")
            st.markdown(differences)
    with col2:
        if markers := prosody.get("prosodic_markers", {}):
            st.markdown(f"**{t('prosodic_markers', lang)}:**")
            for key, label in _MARKERS:
                if key in markers:
                    st.markdown(f"• **{t(label, lang)}:** {markers[key]}")

    if metrics := prosody.get("quantitative_metrics"):
        st.divider()
        _render_measurements(metrics, lang)


def _render_measurements(metrics: dict[str, Any], lang: Lang) -> None:
    st.markdown(f"**{t('detailed_measurements', lang)}**")
    col1, col2, col3 = st.columns(3)
    with col1:
        if pitch := metrics.get("pitch"):
            st.metric(t("mean_pitch", lang), f"{pitch.get('mean_hz', 0):.1f} Hz")
            st.metric(t("pitch_range", lang), f"{pitch.get('range_hz', 0):.1f} Hz")
            st.caption(t("pitch_caption", lang))
    with col2:
        if rate := metrics.get("speaking_rate"):
            st.metric(t("syllables_per_second", lang), f"{rate.get('syllables_per_second', 0):.2f}")
            st.caption(t("rate_caption", lang))
    with col3:
        if voice := metrics.get("voice_quality"):
            st.markdown(f"**{t('voice_quality', lang)}:** {voice.get('type', 'Unknown')}")
            st.markdown(f"**{t('brightness', lang)}:** {voice.get('brightness', 'Unknown')}")
            st.caption(t("voice_caption", lang))
