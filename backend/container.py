"""Composition root: wires the loaded model adapters into the application services."""

import logging

from backend.core.config import Settings
from backend.infrastructure.ml.registry import ModelRegistry
from backend.services.conversation import ConversationAnalysisService
from backend.services.inference_gate import InferenceGate
from backend.services.streaming import SessionLimiter
from backend.services.translation import TranslationService

logger = logging.getLogger(__name__)


class Container:
    def __init__(self, settings: Settings, registry: ModelRegistry):
        self.settings = settings
        self.registry = registry
        self.gate = InferenceGate()
        self.sessions = SessionLimiter(settings.stream_max_sessions)
        self.loading = False
        self.translator = TranslationService(None)
        self.conversation: ConversationAnalysisService | None = None

    @property
    def ready(self) -> bool:
        return self.conversation is not None

    def load(self) -> None:
        """Load models (blocking) and build the services that depend on them."""
        self.loading = True
        try:
            self.registry.load_all()
            self.build_services()
        finally:
            self.loading = False

    def build_services(self) -> None:
        r = self.registry
        self.translator = TranslationService(r.text_llm)
        if r.audio_llm is None:
            logger.error("Audio model unavailable; analysis endpoints will return 503")
            return
        self.conversation = ConversationAnalysisService(r.audio_llm, r.diarizer, self.translator)
        logger.info("Services ready")
