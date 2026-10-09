"""Turn raw diarization turns into per-speaker statistics and a timeline."""

import re
from collections.abc import Iterable

from backend.domain.entities import (
    DiarizationInfo,
    Segment,
    SpeakerStatistics,
    SpeakerTurn,
    TimelineTurn,
)

DIARIZATION_METHOD = "pyannote-community-1"
QUICK_RESPONSE_GAP_S = 0.5

_SPEAKER_LABEL = re.compile(r"SPEAKER[_\s]+(\d+)", re.IGNORECASE)


def normalize_speaker_label(label: str) -> str:
    """``SPEAKER_00`` → ``speaker_0``; other labels are lower-cased."""
    match = _SPEAKER_LABEL.match(label)
    if match:
        return f"speaker_{int(match.group(1))}"
    return label.lower()


def build_diarization_info(turns: Iterable[SpeakerTurn], total_duration: float) -> DiarizationInfo:
    segments: list[Segment] = []
    speaking_time: dict[str, float] = {}

    for turn in turns:
        speaker = normalize_speaker_label(turn.speaker)
        duration = turn.end - turn.start
        segments.append({"speaker": speaker, "start": turn.start, "end": turn.end, "duration": duration})
        speaking_time[speaker] = speaking_time.get(speaker, 0.0) + duration

    segments.sort(key=lambda s: s["start"])
    speakers = sorted(speaking_time)

    statistics: dict[str, SpeakerStatistics] = {}
    for speaker in speakers:
        total = speaking_time[speaker]
        num_turns = sum(1 for s in segments if s["speaker"] == speaker)
        statistics[speaker] = {
            "total_speaking_time": total,
            "speaking_time_percentage": (total / total_duration * 100) if total_duration > 0 else 0,
            "num_turns": num_turns,
            "average_turn_duration": total / num_turns if num_turns > 0 else 0,
        }

    return {
        "speakers": speakers,
        "num_speakers": len(speakers),
        "segments": segments,
        "statistics": statistics,
        "timeline": build_timeline(segments),
        "total_duration": total_duration,
        "diarization_method": DIARIZATION_METHOD,
    }


def build_timeline(segments: list[Segment]) -> list[TimelineTurn]:
    """Chronological turns, annotated with the gap or overlap to the previous turn."""
    timeline: list[TimelineTurn] = []
    for i, segment in enumerate(segments):
        turn: TimelineTurn = {
            "turn_number": i + 1,
            "speaker": segment["speaker"],
            "start": segment["start"],
            "end": segment["end"],
            "duration": segment["duration"],
        }
        if i > 0:
            gap = segment["start"] - segments[i - 1]["end"]
            if gap < 0:
                turn["overlap"] = True
                turn["overlap_duration"] = abs(gap)
            elif gap < QUICK_RESPONSE_GAP_S:
                turn["quick_response"] = True
                turn["gap"] = gap
            else:
                turn["gap"] = gap
        timeline.append(turn)
    return timeline
