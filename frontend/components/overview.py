"""Conversation-level sections: overview metrics, topics, summary and the detailed report."""

from typing import Any

import streamlit as st

from frontend.core.i18n import Lang, t
from frontend.utils.formatting import format_time


def render_overview(conv: dict[str, Any], lang: Lang, duration_s: float | None) -> None:
    st.markdown(f"### {t('conv_overview', lang)}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(t("overall_sentiment", lang), conv.get("overall_sentiment", "Unknown"))
        st.caption(t("sentiment_caption", lang))
    with col2:
        st.metric(t("quality", lang), conv.get("conversation_quality", "Unknown"))
        st.caption(t("quality_caption", lang))
    with col3:
        duration = format_time(duration_s, lang) if duration_s else conv.get("duration_estimate", "Unknown")
        st.metric(t("duration", lang), duration)
        st.caption(t("duration_caption", lang))

    if topics := conv.get("main_topics", []):
        st.markdown(f"**{t('main_topics', lang)}:**")
        for topic in topics:
            st.markdown(f"• {topic}")

    if turning_points := conv.get("turning_points", []):
        st.markdown(f"**{t('key_moments', lang)}:**")
        for point in turning_points:
            st.markdown(f"• {point}")

    if summary := conv.get("conversation_summary", ""):
        st.markdown(f"**{t('summary', lang)}:**")
        st.info(summary)


def render_detailed_analysis(text: str, lang: Lang) -> None:
    st.markdown(f"### {t('detailed_report', lang)}")
    st.markdown(text)
