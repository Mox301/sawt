"""Use case: analyse a multi-speaker conversation."""

import logging
from datetime import UTC, datetime
from typing import Any

from backend.domain.acoustic import extract_acoustic_features
from backend.domain.diarization import build_diarization_info
from backend.domain.parsing import parse_conversation
from backend.domain.prosody import add_acoustic_metrics, apply_turn_taking, override_duration
from backend.domain.turn_taking import analyze_turn_taking
from backend.infrastructure.audio_io import PreparedAudio
from backend.infrastructure.ml.interfaces import AudioLLM, Diarizer
from backend.prompts.conversation import build_conversation_prompt
from backend.services.translation import TranslationService

logger = logging.getLogger(__name__)

MAX_NEW_TOKENS = 4096
MIN_SPEAKERS, MAX_SPEAKERS = 1, 10


class ConversationAnalysisService:
    """Diarization + acoustic features + audio-LLM analysis, merged into one result."""

    def __init__(self, audio_llm: AudioLLM, diarizer: Diarizer | None, translator: TranslationService):
        self.audio_llm = audio_llm
        self.diarizer = diarizer
        self.translator = translator

    def analyze(self, audio: PreparedAudio, filename: str, translate: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {
            "analysis": {},
            "diarization_info": self._diarize(audio),
            "acoustic_features": extract_acoustic_features(audio.waveform, audio.sample_rate),
            "metadata": {
                "audio_filename": filename,
                "processing_timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
            },
        }

        prompt = build_conversation_prompt(result["diarization_info"])
        analysis = parse_conversation(self.audio_llm.generate(audio.path, prompt, MAX_NEW_TOKENS))
        result["analysis"] = analysis

        add_acoustic_metrics(result, analysis)
        override_duration(result, analysis)
        if "speakers" in result["diarization_info"]:
            apply_turn_taking(result, analysis, analyze_turn_taking(result["diarization_info"]))

        logger.info("Conversation analysis complete (%s)", filename)
        return self.translator.translate(result) if translate else result

    def _diarize(self, audio: PreparedAudio) -> dict[str, Any]:
        if self.diarizer is None:
            return {"error": "Diarization model not loaded", "note": "Diarization unavailable"}
        try:
            turns = self.diarizer.diarize(audio.waveform, audio.sample_rate, MIN_SPEAKERS, MAX_SPEAKERS)
            return dict(build_diarization_info(turns, audio.duration_s))
        except Exception as e:
            logger.warning("Diarization failed: %s", e)
            return {"error": str(e), "note": "Diarization failed"}
