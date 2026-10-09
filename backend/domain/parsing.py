"""Parse and normalise the audio LLM's JSON output.

The model is asked for a single JSON object. ``extract_json_object`` takes the
outermost ``{...}`` span; if strict parsing fails it retries after removing
``//`` comments and trailing commas (both appear in the prompt's example, and
models sometimes copy them). Normalisation then coerces every field to the
expected type and allowed values, so clients always receive the same shape.
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

VALID_SENTIMENTS = ["Positive", "Negative", "Neutral", "Mixed", "Unknown"]
VALID_SPEAKER_SENTIMENTS = ["Positive", "Negative", "Neutral"]
VALID_QUALITY = ["Coherent", "Somewhat Coherent", "Fragmented", "Unknown"]
VALID_PITCH = ["High", "Medium", "Low", "Variable", "Unknown"]
VALID_RATE = ["Fast", "Moderate", "Slow", "Variable", "Unknown"]
VALID_ENERGY = ["High", "Moderate", "Low", "Variable", "Unknown"]
VALID_RAPPORT = ["High", "Medium", "Low", "Unknown"]


class LLMOutputError(ValueError):
    """The model output does not contain the expected JSON object."""


def extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise LLMOutputError("No JSON object found in response")
    candidate = text[start : end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as strict_error:
        try:
            return json.loads(_relax_json(candidate))
        except json.JSONDecodeError:
            raise LLMOutputError(str(strict_error)) from strict_error


def _relax_json(text: str) -> str:
    """Drop ``//`` line comments and trailing commas, leaving string contents untouched."""
    out: list[str] = []
    in_string = escaped = False
    i = 0
    while i < len(text):
        ch = text[i]
        if in_string:
            out.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        elif ch == '"':
            in_string = True
            out.append(ch)
        elif text.startswith("//", i):
            newline = text.find("\n", i)
            i = len(text) if newline == -1 else newline
            continue
        elif ch == "," and _next_significant(text, i + 1) in ("}", "]"):
            pass  # trailing comma
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def _next_significant(text: str, i: int) -> str:
    """Next character that is not whitespace or inside a ``//`` comment."""
    while i < len(text):
        if text[i].isspace():
            i += 1
        elif text.startswith("//", i):
            newline = text.find("\n", i)
            if newline == -1:
                return ""
            i = newline
        else:
            return text[i]
    return ""


def parse_conversation(text: str) -> dict[str, Any]:
    try:
        raw = extract_json_object(text)
        result = _validate_conversation(raw)
        logger.info("Parsed conversation analysis (%d speakers)", len(result["speaker_analysis"]))
        return result
    except (LLMOutputError, ValueError, TypeError, AttributeError) as e:
        logger.error("Failed to parse conversation analysis: %s", e)
        return conversation_fallback(text, str(e))


def _validate_conversation(raw: dict[str, Any]) -> dict[str, Any]:
    for key in ("conversation_analysis", "speaker_analysis", "prosody_analysis", "interaction_analysis"):
        if key not in raw:
            raise ValueError(f"Missing '{key}' field")
    if not isinstance(raw["speaker_analysis"], list):
        raise ValueError("'speaker_analysis' must be a list")

    return {
        "conversation_analysis": _conversation_section(raw["conversation_analysis"]),
        "speaker_analysis": [_speaker(s) for s in raw["speaker_analysis"]],
        "prosody_analysis": _prosody_section(raw["prosody_analysis"]),
        "interaction_analysis": _interaction_section(raw["interaction_analysis"]),
        "detailed_analysis": (
            str(raw["detailed_analysis"]).strip() if "detailed_analysis" in raw else "No detailed analysis provided."
        ),
    }


def _one_of(value: Any, allowed: list[str], default: str) -> Any:
    return value if value in allowed else default


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _conversation_section(conv: dict[str, Any]) -> dict[str, Any]:
    return {
        "overall_sentiment": _one_of(conv.get("overall_sentiment", "Unknown"), VALID_SENTIMENTS, "Unknown"),
        "main_topics": _list(conv.get("main_topics", [])),
        "conversation_summary": str(conv.get("conversation_summary", "No summary provided.")),
        "turning_points": _list(conv.get("turning_points", [])),
        "conversation_quality": _one_of(conv.get("conversation_quality", "Unknown"), VALID_QUALITY, "Unknown"),
        "duration_estimate": str(conv.get("duration_estimate", "Unknown")),
    }


def _speaker(speaker: dict[str, Any]) -> dict[str, Any]:
    return {
        "speaker_id": str(speaker.get("speaker_id", "Unknown Speaker")),
        "sentiment": _one_of(speaker.get("sentiment", "Neutral"), VALID_SPEAKER_SENTIMENTS, "Neutral"),
        "speaking_style": str(speaker.get("speaking_style", "Not described")),
        "role": str(speaker.get("role", "Unknown")),
        "emotional_state": str(speaker.get("emotional_state", "Not described")),
        "characteristic_phrases": _list(speaker.get("characteristic_phrases", [])),
        "speaking_time_percentage": str(speaker.get("speaking_time_percentage", "Unknown")),
        "key_contributions": str(speaker.get("key_contributions", "Not specified")),
    }


def _prosody_section(prosody: dict[str, Any]) -> dict[str, Any]:
    markers = prosody.get("prosodic_markers", {})
    if not isinstance(markers, dict):
        markers = {}
    return {
        "overall_pitch": _one_of(prosody.get("overall_pitch", "Unknown"), VALID_PITCH, "Unknown"),
        "overall_speaking_rate": _one_of(prosody.get("overall_speaking_rate", "Unknown"), VALID_RATE, "Unknown"),
        "overall_energy": _one_of(prosody.get("overall_energy", "Unknown"), VALID_ENERGY, "Unknown"),
        "tone_quality": str(prosody.get("tone_quality", "Not described")),
        "emotional_progression": str(prosody.get("emotional_progression", "Not described")),
        "notable_acoustic_features": _list(prosody.get("notable_acoustic_features", [])),
        "speaker_prosody_differences": str(prosody.get("speaker_prosody_differences", "Not described")),
        "prosodic_markers": {
            "emphasis_usage": str(markers.get("emphasis_usage", "Not described")),
            "pause_patterns": str(markers.get("pause_patterns", "Not described")),
            "intonation_variety": str(markers.get("intonation_variety", "Unknown")),
        },
    }


def _interaction_section(interaction: dict[str, Any]) -> dict[str, Any]:
    engagement = interaction.get("engagement_levels", {})
    return {
        "turn_taking_style": interaction.get("turn_taking_style", "Calculating..."),
        "conversational_balance": str(interaction.get("conversational_balance", "Unknown")),
        "rapport_level": _one_of(interaction.get("rapport_level", "Unknown"), VALID_RAPPORT, "Unknown"),
        "cooperation_vs_conflict": str(interaction.get("cooperation_vs_conflict", "Unknown")),
        "dominance_pattern": str(interaction.get("dominance_pattern", "Not described")),
        "engagement_levels": engagement if isinstance(engagement, dict) else {},
        "interruptions": interaction.get("interruptions", "Calculating..."),
        "conversation_flow": str(interaction.get("conversation_flow", "Not described")),
        "interaction_quality": str(interaction.get("interaction_quality", "Unknown")),
    }


def conversation_fallback(text: str, error: str) -> dict[str, Any]:
    """Minimal valid result when the model output cannot be parsed."""
    return {
        "conversation_analysis": {
            "overall_sentiment": "Unknown",
            "main_topics": [],
            "conversation_summary": f"Failed to parse response. Error: {error}",
            "turning_points": [],
            "conversation_quality": "Unknown",
            "duration_estimate": "Unknown",
        },
        "speaker_analysis": [
            {
                "speaker_id": "Speaker 1",
                "sentiment": "Neutral",
                "speaking_style": "Could not analyze",
                "role": "Unknown",
                "emotional_state": "Could not determine",
                "characteristic_phrases": [],
                "speaking_time_percentage": "Unknown",
                "key_contributions": "Analysis failed",
            }
        ],
        "prosody_analysis": {
            "overall_pitch": "Unknown",
            "overall_speaking_rate": "Unknown",
            "overall_energy": "Unknown",
            "tone_quality": "Could not analyze",
            "emotional_progression": "Could not analyze",
            "notable_acoustic_features": [],
            "speaker_prosody_differences": "Could not analyze",
            "prosodic_markers": {
                "emphasis_usage": "Unknown",
                "pause_patterns": "Unknown",
                "intonation_variety": "Unknown",
            },
        },
        "interaction_analysis": {
            "turn_taking_style": "Calculating...",
            "conversational_balance": "Unknown",
            "rapport_level": "Unknown",
            "cooperation_vs_conflict": "Unknown",
            "dominance_pattern": "Could not determine",
            "engagement_levels": {},
            "interruptions": "Calculating...",
            "conversation_flow": "Could not analyze",
            "interaction_quality": "Unknown",
        },
        "detailed_analysis": f"Analysis failed. Raw response excerpt: {text.strip()[:200]}...",
        "parsing_error": error,
        "raw_response_excerpt": text.strip()[:500],
    }
