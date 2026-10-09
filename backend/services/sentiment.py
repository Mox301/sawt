"""Use case: classify the overall sentiment of a recording."""

from typing import Any

from backend.domain.parsing import parse_sentiment
from backend.infrastructure.audio_io import PreparedAudio
from backend.infrastructure.ml.interfaces import AudioLLM
from backend.prompts.sentiment import SENTIMENT_ANALYSIS_PROMPT
from backend.services.translation import TranslationService

MAX_NEW_TOKENS = 2048


class SentimentAnalysisService:
    def __init__(self, audio_llm: AudioLLM, translator: TranslationService):
        self.audio_llm = audio_llm
        self.translator = translator

    def analyze(self, audio: PreparedAudio, translate: bool = False) -> dict[str, Any]:
        result = parse_sentiment(self.audio_llm.generate(audio.path, SENTIMENT_ANALYSIS_PROMPT, MAX_NEW_TOKENS))
        return self.translator.translate(result) if translate else result
