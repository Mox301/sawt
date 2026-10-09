"""Loads the configured models and reports their status.

Each model loads independently: a failed translation or diarization model leaves
the service usable with reduced output instead of taking it down.
"""

import logging
from dataclasses import dataclass, field
from typing import Literal

from backend.core.config import Settings
from backend.infrastructure.ml.interfaces import AudioLLM, Diarizer, TextLLM

logger = logging.getLogger(__name__)

State = Literal["pending", "loading", "ready", "failed", "disabled"]


@dataclass
class ModelStatus:
    name: str
    state: State = "pending"
    error: str | None = None


@dataclass
class ModelRegistry:
    settings: Settings
    device: str = "unknown"
    audio_llm: AudioLLM | None = None
    diarizer: Diarizer | None = None
    text_llm: TextLLM | None = None
    status: dict[str, ModelStatus] = field(default_factory=dict)

    def __post_init__(self) -> None:
        s = self.settings
        translation_name = s.ollama_model if s.translation_backend == "ollama" else s.translation_model
        self.status = {
            "audio_llm": ModelStatus(s.audio_model),
            "diarization": ModelStatus(s.diarization_model, "pending" if s.enable_diarization else "disabled"),
            "translation": ModelStatus(translation_name, "disabled" if s.translation_backend == "off" else "pending"),
        }

    def load_all(self) -> None:
        s = self.settings
        try:
            # Imported lazily so the API can start (and tests run) without torch installed.
            from backend.infrastructure.ml.device import attention_implementation, resolve_device, resolve_dtype

            self.device = resolve_device(s.device)
            dtype = resolve_dtype(self.device, s.dtype)
        except Exception as e:
            logger.exception("Could not set up the model runtime")
            for status in self.status.values():
                if status.state == "pending":
                    status.state, status.error = "failed", str(e)
            return
        logger.info("Loading models on %s (%s)", self.device, dtype)

        def load_voxtral():
            from backend.infrastructure.ml.voxtral import VoxtralAudioLLM

            self.audio_llm = VoxtralAudioLLM(s.audio_model, self.device, dtype, attention_implementation(self.device))

        def load_pyannote():
            from backend.infrastructure.ml.pyannote import PyannoteDiarizer

            self.diarizer = PyannoteDiarizer(s.diarization_model, self.device)

        def load_translation():
            if s.translation_backend == "ollama":
                from backend.infrastructure.ml.ollama_text import OllamaTextLLM

                self.text_llm = OllamaTextLLM(s.ollama_url, s.ollama_model)
            else:
                from backend.infrastructure.ml.transformers_text import TransformersTextLLM

                self.text_llm = TransformersTextLLM(s.translation_model, self.device)

        self._load("audio_llm", load_voxtral)
        self._load("diarization", load_pyannote)
        self._load("translation", load_translation)

    def _load(self, key: str, loader) -> None:
        status = self.status[key]
        if status.state == "disabled":
            return
        status.state = "loading"
        try:
            loader()
            status.state = "ready"
        except Exception as e:
            logger.exception("Failed to load %s (%s)", key, status.name)
            status.state, status.error = "failed", str(e)
