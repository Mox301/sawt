"""Ports the application services depend on. Adapters in this package implement them;
tests use in-memory fakes."""

from collections.abc import Sequence
from typing import Protocol

import numpy as np

from backend.domain.entities import SpeakerTurn


class AudioLLM(Protocol):
    """An audio-language model that answers a text prompt about an audio file."""

    def generate(self, audio_path: str, prompt: str, max_new_tokens: int) -> str: ...


class TextLLM(Protocol):
    """A text model used for translation."""

    def generate_batch(self, prompts: Sequence[str], max_new_tokens: int) -> list[str]: ...


class Diarizer(Protocol):
    """Speaker diarization: who spoke when."""

    def diarize(
        self, waveform: np.ndarray, sample_rate: int, min_speakers: int = 1, max_speakers: int = 10
    ) -> list[SpeakerTurn]: ...
