"""Pick one language out of an API response and expose its sections.

``POST /api/v1/conversations/analyze`` returns either ``{"EN": result, "AR": result}`` (translated)
or a single English ``result``. Both shapes are read the same way here, so the Arabic
UI still works on an English-only result (Arabic labels, English content).
"""

from dataclasses import dataclass
from typing import Any

from frontend.core.i18n import Lang

NO_DETAILED_ANALYSIS = "No detailed analysis provided."
_PLACEHOLDERS = frozenset({"Unknown", "Not described", "Not specified", NO_DETAILED_ANALYSIS})

# Text fields the components hide when they hold an (English) placeholder.
_HIDDEN_SPEAKER_FIELDS = ("speaking_style", "emotional_state", "key_contributions")
_HIDDEN_INTERACTION_FIELDS = ("conversational_balance", "interruptions", "dominance_pattern")


@dataclass(frozen=True)
class ResultView:
    conversation: dict[str, Any]
    speakers: list[dict[str, Any]]
    prosody: dict[str, Any]
    interaction: dict[str, Any]
    detailed_analysis: str
    diarization: dict[str, Any]
    duration_s: float | None

    @property
    def num_speakers(self) -> int:
        return self.diarization.get("num_speakers", 1)


def is_bilingual(data: dict[str, Any]) -> bool:
    return "EN" in data and "AR" in data


def parse_result(data: dict[str, Any], lang: Lang) -> ResultView:
    result = data[lang] if is_bilingual(data) else data
    analysis = result.get("analysis", {})
    if lang == "AR" and is_bilingual(data):
        analysis = _hide_translated_placeholders(analysis, data["EN"].get("analysis", {}))
    diarization = result.get("diarization_info", {})
    detailed = analysis.get("detailed_analysis", "")
    return ResultView(
        conversation=analysis.get("conversation_analysis", {}),
        speakers=analysis.get("speaker_analysis", []),
        prosody=analysis.get("prosody_analysis", {}),
        interaction=analysis.get("interaction_analysis", {}),
        detailed_analysis="" if detailed == NO_DETAILED_ANALYSIS else detailed,
        diarization=diarization,
        duration_s=result.get("acoustic_features", {}).get("duration") or diarization.get("total_duration"),
    )


def _hide_translated_placeholders(arabic: dict[str, Any], english: dict[str, Any]) -> dict[str, Any]:
    """Blank Arabic fields whose English twin is a placeholder, so both views hide the same fields.

    Translated placeholders never match the English strings the components compare against.
    Translation keeps list order, so speakers pair up by position. Returns a copy; ``arabic`` is untouched.
    """
    speakers = zip(arabic.get("speaker_analysis", []), english.get("speaker_analysis", []), strict=True)
    return {
        **_blank_placeholders(arabic, english, ("detailed_analysis",)),
        "speaker_analysis": [_blank_placeholders(ar, en, _HIDDEN_SPEAKER_FIELDS) for ar, en in speakers],
        "interaction_analysis": _blank_placeholders(
            arabic.get("interaction_analysis", {}), english.get("interaction_analysis", {}), _HIDDEN_INTERACTION_FIELDS
        ),
    }


def _blank_placeholders(arabic: dict[str, Any], english: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    return {**arabic, **{key: "" for key in keys if english.get(key) in _PLACEHOLDERS}}
