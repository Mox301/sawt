"""Shapes of the analysis results.

These are ``TypedDict``s rather than classes on purpose: the API returns plain JSON
and these types document (and let type-checkers verify) the exact keys clients
receive, without changing them.
"""

from enum import StrEnum
from typing import Any, NamedTuple, NotRequired, TypedDict


class SpeakerTurn(NamedTuple):
    """One raw diarization turn as produced by a diarizer."""

    start: float
    end: float
    speaker: str


class Segment(TypedDict):
    speaker: str
    start: float
    end: float
    duration: float


class TimelineTurn(TypedDict):
    turn_number: int
    speaker: str
    start: float
    end: float
    duration: float
    gap: NotRequired[float]
    quick_response: NotRequired[bool]
    overlap: NotRequired[bool]
    overlap_duration: NotRequired[float]


class SpeakerStatistics(TypedDict):
    total_speaking_time: float
    speaking_time_percentage: float
    num_turns: int
    average_turn_duration: float


class DiarizationInfo(TypedDict):
    speakers: list[str]
    num_speakers: int
    segments: list[Segment]
    statistics: dict[str, SpeakerStatistics]
    timeline: list[TimelineTurn]
    total_duration: float
    diarization_method: str


class TurnTakingStyle(StrEnum):
    SMOOTH = "Smooth"
    OVERLAPPING = "Overlapping"
    INTERRUPTED = "Interrupted"
    SEQUENTIAL = "Sequential"
    MIXED = "Mixed"
    MONOLOGUE = "Monologue"
    UNKNOWN = "Unknown"


class TurnTakingMetrics(TypedDict, total=False):
    turn_taking_style: str
    num_turns: int
    num_speaker_switches: int
    avg_gap_between_turns_s: float
    num_overlaps: int
    overlap_percentage: float
    avg_overlap_duration_s: float
    num_interruptions: int
    turn_transition_speed: str
    longest_gap_s: float
    shortest_gap_s: float
    note: str
    error: str


class ConversationResult(TypedDict):
    """Response of ``POST /v1/conversation`` (before optional translation)."""

    analysis: dict[str, Any]
    diarization_info: dict[str, Any]
    acoustic_features: dict[str, Any]
    metadata: dict[str, Any]
    turn_taking_metrics: NotRequired[TurnTakingMetrics]


class SentimentResult(TypedDict):
    """Response of ``POST /v1/sentiment`` (before optional translation)."""

    sentiment: str
    analysis: str
