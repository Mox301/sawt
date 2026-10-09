"""Interaction dynamics section (shown only for conversations with more than one speaker)."""

from typing import Any

import streamlit as st

from frontend.core.i18n import Lang, t
from frontend.utils.formatting import format_speaker_label, format_text_with_speakers, format_time


def render_dynamics(interaction: dict[str, Any], lang: Lang) -> None:
    st.markdown(f"### {t('interaction_dynamics', lang)}")
    st.caption(t("interaction_caption", lang))
    _render_turn_taking(interaction, lang)
    st.divider()
    _render_relationship(interaction, lang)
    st.divider()
    _render_conversation_dynamics(interaction, lang)


def _render_turn_taking(interaction: dict[str, Any], lang: Lang) -> None:
    st.markdown(f"#### {t('turn_taking_patterns', lang)}")
    details = interaction.get("turn_taking_details", {})
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t("total_turns", lang), details.get("num_turns", 0))
    col2.metric(t("speaker_switches", lang), details.get("num_speaker_switches", 0))
    col3.metric(t("avg_gap", lang), format_time(details.get("avg_gap_between_turns_s", 0), lang))
    col4.metric(t("overlaps", lang), f"{details.get('num_overlaps', 0)} ({details.get('overlap_percentage', 0):.1f}%)")

    balance = interaction.get("conversational_balance", "Unknown")
    if balance and balance != "Unknown":
        st.info(f"**{t('balance', lang)}:** {format_text_with_speakers(balance, lang)}")


def _render_relationship(interaction: dict[str, Any], lang: Lang) -> None:
    st.markdown(f"#### {t('relationship_quality', lang)}")
    col1, col2 = st.columns(2)
    col1.metric(t("rapport", lang), interaction.get("rapport_level", "Unknown"))
    col2.metric(t("cooperation", lang), interaction.get("cooperation_vs_conflict", "Unknown"))

    col1, col2 = st.columns(2)
    interruptions = interaction.get("interruptions", "Unknown")
    if interruptions and interruptions != "Unknown":
        col1.markdown(f"**{t('interruptions', lang)}:** {interruptions}")
    if style := interaction.get("turn_taking_style", ""):
        col2.markdown(f"**{t('turn_taking_style', lang)}:** {style}")


def _render_conversation_dynamics(interaction: dict[str, Any], lang: Lang) -> None:
    st.markdown(f"#### {t('conversation_dynamics', lang)}")
    col1, col2 = st.columns(2)
    if flow := interaction.get("conversation_flow", ""):
        col1.markdown(f"**{t('conversation_flow', lang)}:**")
        col1.write(flow)
    if quality := interaction.get("interaction_quality", ""):
        col2.markdown(f"**{t('interaction_quality', lang)}:**")
        col2.write(quality)

    dominance = interaction.get("dominance_pattern", "")
    if dominance and dominance != "Not described":
        st.warning(f"**{t('dominance_pattern', lang)}:**\n\n{format_text_with_speakers(dominance, lang)}")

    if engagement := interaction.get("engagement_levels", {}):
        st.markdown(f"**{t('engagement_levels', lang)}:**")
        for col, (speaker, level) in zip(st.columns(len(engagement)), engagement.items(), strict=True):
            col.metric(format_speaker_label(speaker, lang), level)
