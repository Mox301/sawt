"""Turn-taking metrics (gaps, overlaps, interruptions) from diarization segments."""

import logging
from typing import Any

from backend.domain.entities import TurnTakingMetrics, TurnTakingStyle

logger = logging.getLogger(__name__)

INTERRUPTION_MIN_OVERLAP_S = 0.3
INTERRUPTION_MIN_TURN_S = 1.0
OVERLAPPING_ABOVE_PCT = 10
INTERRUPTED_RATE_ABOVE = 0.2
SEQUENTIAL_GAP_ABOVE_S = 0.5
SMOOTH_OVERLAP_BELOW_PCT = 3
FAST_TRANSITION_BELOW_S = 0.2
MODERATE_TRANSITION_BELOW_S = 0.5


def analyze_turn_taking(diarization_info: dict[str, Any]) -> TurnTakingMetrics:
    try:
        segments = sorted(diarization_info.get("segments") or [], key=lambda s: s["start"])
        if not diarization_info.get("speakers") or not segments:
            return {
                "turn_taking_style": TurnTakingStyle.UNKNOWN.value,
                "note": "Diarization data not available for turn-taking analysis",
            }

        if len(segments) < 2:
            return {
                "turn_taking_style": TurnTakingStyle.MONOLOGUE.value,
                "num_turns": len(segments),
                "num_speaker_switches": 0,
                "avg_gap_between_turns_s": 0,
                "num_overlaps": 0,
                "overlap_percentage": 0,
                "num_interruptions": 0,
                "turn_transition_speed": "N/A",
                "note": "Only one speaker or insufficient segments",
            }

        return _metrics(segments)
    except Exception as e:
        logger.error("Turn-taking analysis failed: %s", e)
        return {"turn_taking_style": TurnTakingStyle.UNKNOWN.value, "error": str(e)}


def _metrics(segments: list[dict[str, Any]]) -> TurnTakingMetrics:
    gaps: list[float] = []
    overlaps: list[float] = []
    interruptions = 0
    speaker_switches = 0

    for current, nxt in zip(segments, segments[1:], strict=False):
        if current["speaker"] != nxt["speaker"]:
            speaker_switches += 1
        gap = nxt["start"] - current["end"]
        if gap > 0:
            gaps.append(gap)
        elif gap < 0:
            overlaps.append(abs(gap))
            if abs(gap) > INTERRUPTION_MIN_OVERLAP_S and current["duration"] > INTERRUPTION_MIN_TURN_S:
                interruptions += 1

    num_turns = len(segments)
    avg_gap = sum(gaps) / len(gaps) if gaps else 0
    avg_overlap = sum(overlaps) / len(overlaps) if overlaps else 0
    total_duration = max(s["end"] for s in segments)
    overlap_pct = (sum(overlaps) / total_duration * 100) if total_duration > 0 else 0

    if avg_gap < FAST_TRANSITION_BELOW_S:
        speed = "Fast"
    elif avg_gap < MODERATE_TRANSITION_BELOW_S:
        speed = "Moderate"
    else:
        speed = "Slow"

    return {
        "turn_taking_style": classify_style(overlap_pct, avg_gap, interruptions, num_turns),
        "num_turns": num_turns,
        "num_speaker_switches": speaker_switches,
        "avg_gap_between_turns_s": round(avg_gap, 2),
        "num_overlaps": len(overlaps),
        "overlap_percentage": round(overlap_pct, 1),
        "avg_overlap_duration_s": round(avg_overlap, 2) if overlaps else 0,
        "num_interruptions": interruptions,
        "turn_transition_speed": speed,
        "longest_gap_s": round(max(gaps), 2) if gaps else 0,
        "shortest_gap_s": round(min(gaps), 2) if gaps else 0,
    }


def classify_style(overlap_pct: float, avg_gap: float, interruptions: int, num_turns: int) -> str:
    if overlap_pct > OVERLAPPING_ABOVE_PCT:
        return TurnTakingStyle.OVERLAPPING.value
    if num_turns > 0 and interruptions / num_turns > INTERRUPTED_RATE_ABOVE:
        return TurnTakingStyle.INTERRUPTED.value
    if avg_gap > SEQUENTIAL_GAP_ABOVE_S:
        return TurnTakingStyle.SEQUENTIAL.value
    if overlap_pct < SMOOTH_OVERLAP_BELOW_PCT and avg_gap < SEQUENTIAL_GAP_ABOVE_S:
        return TurnTakingStyle.SMOOTH.value
    return TurnTakingStyle.MIXED.value
