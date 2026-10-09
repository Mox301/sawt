"""Pick one language out of an API response and expose its sections.

``POST /api/v1/conversations/analyze`` returns either ``{"EN": result, "AR": result}`` (translated)
or a single English ``result``. Both shapes are read the same way here, so the Arabic
UI still works on an English-only result (Arabic labels, English content).
"""

from dataclasses import dataclass
from typing import Any

from frontend.core.i18n import Lang

NO_DETAILED_ANALYSIS = "No detailed analysis provided."


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
