"""Shared fixtures: realistic API responses shaped like the backend's ``/v1/conversation`` output."""

import json
from collections.abc import Callable
from typing import Any

import pytest
import requests


def _make_response(status: int, payload: Any = None, text: str = "") -> requests.Response:
    """A real ``requests.Response`` carrying ``payload`` as JSON (or ``text`` as the raw body)."""
    response = requests.Response()
    response.status_code = status
    response._content = (json.dumps(payload) if payload is not None else text).encode()
    response.headers["Content-Type"] = "application/json" if payload is not None else "text/plain"
    return response


def _english_result() -> dict[str, Any]:
    return {
        "analysis": {
            "conversation_analysis": {
                "overall_sentiment": "Mixed",
                "main_topics": ["billing", "service outage"],
                "conversation_summary": "speaker_0 reports an outage and speaker_1 offers a refund.",
                "turning_points": ["speaker_1 offers a refund"],
                "conversation_quality": "Coherent",
                "duration_estimate": "42.5 seconds",
            },
            "speaker_analysis": [
                {
                    "speaker_id": "speaker_0",
                    "sentiment": "Negative",
                    "speaking_style": "Frustrated but polite",
                    "role": "Customer",
                    "emotional_state": "Calms down after the offer",
                    "characteristic_phrases": ["this is the third time"],
                    "speaking_time_percentage": "45%",
                    "key_contributions": "Explains the problem",
                },
                {
                    "speaker_id": "speaker_1",
                    "sentiment": "Positive",
                    "speaking_style": "Calm",
                    "role": "Agent",
                    "emotional_state": "Steady",
                    "characteristic_phrases": ["I apologize"],
                    "speaking_time_percentage": "55%",
                    "key_contributions": "Offers a solution",
                },
            ],
            "prosody_analysis": {
                "overall_pitch": "Medium",
                "overall_speaking_rate": "Moderate",
                "overall_energy": "High",
                "tone_quality": "Warm",
                "emotional_progression": "From tense to relaxed",
                "notable_acoustic_features": ["raised voice early on"],
                "speaker_prosody_differences": "speaker_0 is louder",
                "prosodic_markers": {
                    "emphasis_usage": "Moderate",
                    "pause_patterns": "Short",
                    "intonation_variety": "Varied",
                },
                "quantitative_metrics": {
                    "pitch": {"mean_hz": 182.4, "range_hz": 210.7, "std_hz": 35.2, "category": "Medium"},
                    "energy": {"mean_db": 0.061, "std_db": 0.032, "dynamic_range_db": 0.21, "category": "High"},
                    "speaking_rate": {"syllables_per_second": 4.12, "category": "Moderate"},
                    "voice_quality": {
                        "spectral_centroid_hz": 1843.0,
                        "spectral_rolloff_hz": 3920.5,
                        "zero_crossing_rate": 0.083,
                        "brightness": "Balanced",
                        "type": "Clear",
                    },
                },
            },
            "interaction_analysis": {
                "turn_taking_style": "Smooth",
                "conversational_balance": "Balanced, speaker_1 slightly leads",
                "rapport_level": "Medium",
                "cooperation_vs_conflict": "Cooperative",
                "dominance_pattern": "Led by speaker_1",
                "engagement_levels": {"speaker_0": "High", "speaker_1": "High"},
                "interruptions": "Rare",
                "conversation_flow": "Smooth",
                "interaction_quality": "Good",
                "turn_taking_details": {
                    "num_turns": 6,
                    "num_speaker_switches": 5,
                    "avg_gap_between_turns_s": 0.42,
                    "transition_speed": "Moderate",
                    "num_overlaps": 1,
                    "overlap_percentage": 1.2,
                    "num_interruptions": 1,
                },
            },
            "detailed_analysis": "A short support call that ends amicably.",
        },
        "diarization_info": {
            "speakers": ["speaker_0", "speaker_1"],
            "num_speakers": 2,
            "segments": [
                {"speaker": "speaker_0", "start": 0.0, "end": 9.5, "duration": 9.5},
                {"speaker": "speaker_1", "start": 9.9, "end": 21.0, "duration": 11.1},
                {"speaker": "speaker_0", "start": 21.3, "end": 30.0, "duration": 8.7},
                {"speaker": "speaker_1", "start": 29.5, "end": 42.5, "duration": 13.0},
            ],
            "statistics": {
                "speaker_0": {
                    "total_speaking_time": 18.2,
                    "speaking_time_percentage": 42.8,
                    "num_turns": 2,
                    "average_turn_duration": 9.1,
                },
                "speaker_1": {
                    "total_speaking_time": 24.1,
                    "speaking_time_percentage": 56.7,
                    "num_turns": 2,
                    "average_turn_duration": 12.05,
                },
            },
            "timeline": [],
            "total_duration": 42.5,
            "diarization_method": "pyannote-community-1",
        },
        "acoustic_features": {"duration": 42.5},
        "metadata": {"audio_filename": "call.wav", "processing_timestamp": "2026-10-09T12:00:00+00:00"},
        "turn_taking_metrics": {"turn_taking_style": "Smooth", "num_turns": 6, "num_speaker_switches": 5},
    }


def _arabic_result() -> dict[str, Any]:
    result = _english_result()
    conv = result["analysis"]["conversation_analysis"]
    conv["overall_sentiment"] = "مختلط"
    conv["main_topics"] = ["الفواتير", "انقطاع الخدمة"]
    conv["conversation_summary"] = "يبلغ متحدث ٠ عن انقطاع ويعرض متحدث ١ استرداد المبلغ."
    result["analysis"]["detailed_analysis"] = "مكالمة دعم قصيرة تنتهي بشكل ودي."
    return result


@pytest.fixture
def english_result() -> dict[str, Any]:
    return _english_result()


@pytest.fixture
def bilingual_response() -> dict[str, Any]:
    return {"EN": _english_result(), "AR": _arabic_result()}


@pytest.fixture
def untranslated_response() -> dict[str, Any]:
    """What the API returns when translation was requested but the text model is unavailable."""
    result = _english_result()
    result["metadata"]["translation"] = "unavailable"
    return result


@pytest.fixture
def make_response() -> Callable[..., requests.Response]:
    return _make_response
