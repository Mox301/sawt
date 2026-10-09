"""Combine the audio LLM's qualitative analysis with measured signal features.

The LLM describes prosody and interaction in words; librosa and pyannote measure
them. These functions merge the measurements into the LLM result in place:
measured categories fill in fields the LLM left as "Unknown", and the exact
numbers are attached alongside.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

FREQUENT_INTERRUPTIONS_ABOVE = 0.3
OCCASIONAL_INTERRUPTIONS_ABOVE = 0.1


def add_acoustic_metrics(result: dict[str, Any], analysis: dict[str, Any]) -> None:
    """Fill unknown prosody categories and attach ``quantitative_metrics``."""
    acoustic = result.get("acoustic_features", {})
    if "pitch_features" not in acoustic or "prosody_analysis" not in analysis:
        return

    pitch = acoustic.get("pitch_features", {})
    energy = acoustic.get("energy_features", {})
    spectral = acoustic.get("spectral_features", {})
    temporal = acoustic.get("temporal_features", {})
    voice = acoustic.get("voice_quality", {})

    pitch_category = pitch.get("pitch_category", "Unknown")
    energy_category = energy.get("energy_category", "Unknown")
    rate_category = temporal.get("speaking_rate_category", "Unknown")

    prosody = analysis["prosody_analysis"]
    for field, measured in (
        ("overall_pitch", pitch_category),
        ("overall_speaking_rate", rate_category),
        ("overall_energy", energy_category),
    ):
        if prosody.get(field) == "Unknown" and measured != "Unknown":
            prosody[field] = measured

    prosody["quantitative_metrics"] = {
        "pitch": {
            "mean_hz": pitch.get("mean_pitch_hz", 0),
            "range_hz": pitch.get("pitch_range_hz", 0),
            "std_hz": pitch.get("pitch_std_hz", 0),
            "category": pitch_category,
        },
        "energy": {
            # Linear RMS amplitude; the "_db" key names are kept for API compatibility.
            "mean_db": energy.get("mean_energy", 0),
            "std_db": energy.get("energy_std", 0),
            "dynamic_range_db": energy.get("dynamic_range", 0),
            "category": energy_category,
        },
        "speaking_rate": {
            "syllables_per_second": temporal.get("syllables_per_second", 0),
            "category": rate_category,
        },
        "voice_quality": {
            "spectral_centroid_hz": spectral.get("mean_spectral_centroid_hz", 0),
            "spectral_rolloff_hz": spectral.get("mean_spectral_rolloff_hz", 0),
            "zero_crossing_rate": spectral.get("mean_zero_crossing_rate", 0),
            "brightness": spectral.get("brightness", "Unknown"),
            "type": voice.get("voice_type", "Unknown"),
        },
    }


def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    if seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m"


def override_duration(result: dict[str, Any], analysis: dict[str, Any]) -> None:
    """Replace the LLM's duration guess with the measured duration."""
    duration = result.get("acoustic_features", {}).get("duration", 0)
    if duration > 0 and "conversation_analysis" in analysis:
        analysis["conversation_analysis"]["duration_estimate"] = format_duration(duration)


def apply_turn_taking(result: dict[str, Any], analysis: dict[str, Any], metrics: dict[str, Any]) -> None:
    """Attach measured turn-taking metrics and overwrite the LLM's guesses."""
    interaction = analysis.get("interaction_analysis")
    switches = metrics.get("num_speaker_switches", 0)

    if switches <= 0:
        if interaction is not None:
            interaction.pop("turn_taking_style", None)
            interaction.pop("turn_taking_details", None)
            interaction["interruptions"] = "Not Applicable (No speaker switches)"
        return

    result["turn_taking_metrics"] = metrics
    if interaction is None:
        return

    style = metrics.get("turn_taking_style", "Unknown")
    if style != "Unknown":
        interaction["turn_taking_style"] = style

    num_turns = metrics.get("num_turns", 0)
    num_interruptions = metrics.get("num_interruptions", 0)
    rate = num_interruptions / num_turns if num_turns > 0 else 0
    if rate > FREQUENT_INTERRUPTIONS_ABOVE:
        interaction["interruptions"] = "Frequent"
    elif rate > OCCASIONAL_INTERRUPTIONS_ABOVE:
        interaction["interruptions"] = "Occasional"
    elif num_interruptions > 0:
        interaction["interruptions"] = "Rare"
    else:
        interaction["interruptions"] = "None"

    interaction["turn_taking_details"] = {
        "num_turns": num_turns,
        "num_speaker_switches": switches,
        "avg_gap_between_turns_s": metrics.get("avg_gap_between_turns_s", 0),
        "transition_speed": metrics.get("turn_transition_speed", "Unknown"),
        "num_overlaps": metrics.get("num_overlaps", 0),
        "overlap_percentage": metrics.get("overlap_percentage", 0),
        "num_interruptions": num_interruptions,
    }
