"""Plotly figures for the diarization results."""

from typing import Any

import plotly.graph_objects as go

from frontend.core.i18n import Lang, t
from frontend.core.settings import CHART_COLORS
from frontend.utils.formatting import format_speaker_label


def speaker_timeline_figure(diarization: dict[str, Any], lang: Lang) -> go.Figure | None:
    """One horizontal bar per diarization segment, a row per speaker."""
    if "segments" not in diarization:
        return None

    speakers = diarization.get("speakers", [])
    colors = {speaker: CHART_COLORS[i % len(CHART_COLORS)] for i, speaker in enumerate(speakers)}
    start, end, duration = t("start", lang), t("end", lang), t("duration", lang)

    fig = go.Figure()
    for segment in diarization["segments"]:
        label = format_speaker_label(segment["speaker"], lang)
        fig.add_trace(
            go.Scatter(
                x=[segment["start"], segment["end"]],
                y=[label, label],
                mode="lines",
                line={"color": colors.get(segment["speaker"], CHART_COLORS[0]), "width": 20},
                hovertemplate=(
                    f"<b>{label}</b><br>{start}: {segment['start']:.2f}s<br>{end}: {segment['end']:.2f}s"
                    f"<br>{duration}: {segment['duration']:.2f}s<extra></extra>"
                ),
                showlegend=False,
            )
        )
    fig.update_layout(
        xaxis_title=t("chart_time_axis", lang),
        yaxis_title=t("chart_speaker_axis", lang),
        height=200 + len(speakers) * 50,
        hovermode="closest",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def speaking_time_figure(diarization: dict[str, Any], lang: Lang) -> go.Figure | None:
    """Donut chart of each speaker's share of the recording."""
    if "statistics" not in diarization:
        return None

    stats = diarization["statistics"]
    fig = go.Figure(
        go.Pie(
            labels=[format_speaker_label(speaker, lang) for speaker in stats],
            values=[stat.get("speaking_time_percentage", 0) for stat in stats.values()],
            hole=0.4,
            marker={"colors": CHART_COLORS},
        )
    )
    rtl = lang == "AR"
    fig.update_layout(
        title={
            "text": t("speaking_time_distribution", lang),
            "x": 0.95 if rtl else 0.0,
            "xanchor": "right" if rtl else "left",
        },
        height=400,
        showlegend=True,
    )
    return fig
