"""In-memory stand-ins for the model adapters."""

import json
from collections.abc import Sequence

import numpy as np

from backend.domain.entities import SpeakerTurn
from backend.infrastructure.ml.registry import ModelRegistry

CONVERSATION_JSON = {
    "conversation_analysis": {
        "overall_sentiment": "Mixed",
        "main_topics": ["billing", "outage"],
        "conversation_summary": "The customer reports an outage and Speaker 1 resolves it.",
        "turning_points": ["Speaker 1 offers a refund"],
        "conversation_quality": "Coherent",
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
        "overall_pitch": "Unknown",
        "overall_speaking_rate": "Moderate",
        "overall_energy": "Unknown",
        "tone_quality": "Warm",
        "emotional_progression": "From tense to relaxed",
        "notable_acoustic_features": ["raised voice early on"],
        "speaker_prosody_differences": "Speaker 0 is louder",
        "prosodic_markers": {"emphasis_usage": "Moderate", "pause_patterns": "Short", "intonation_variety": "Varied"},
    },
    "interaction_analysis": {
        "turn_taking_style": "Smooth",
        "conversational_balance": "Balanced",
        "rapport_level": "Medium",
        "cooperation_vs_conflict": "Cooperative",
        "dominance_pattern": "Dominated by Speaker 1",
        "engagement_levels": {"speaker_0": "High", "speaker_1": "High"},
        "interruptions": "Rare",
        "conversation_flow": "Smooth",
        "interaction_quality": "Good",
    },
    "detailed_analysis": "A short support call.",
}


class FakeAudioLLM:
    def __init__(self, response: str | None = None):
        self.response = response
        self.calls: list[tuple[str, str, int]] = []

    def generate(self, audio_path: str, prompt: str, max_new_tokens: int) -> str:
        self.calls.append((audio_path, prompt, max_new_tokens))
        if self.response is not None:
            return self.response
        return "```json\n" + json.dumps(CONVERSATION_JSON) + "\n```"


class FakeTextLLM:
    """Echoes the masked English text inside an Arabic marker so tests can trace it."""

    def __init__(self):
        self.prompts: list[str] = []

    def generate_batch(self, prompts: Sequence[str], max_new_tokens: int) -> list[str]:
        self.prompts.extend(prompts)
        return [f"ترجمة[{_source_text(p)}]" for p in prompts]


def _source_text(prompt: str) -> str:
    return prompt.split("النص الإنجليزي:\n", 1)[1].split("\n\nالترجمة العربية:", 1)[0]


class FakeDiarizer:
    def __init__(self, turns: list[SpeakerTurn] | None = None):
        self.turns = turns or [
            SpeakerTurn(0.0, 1.0, "SPEAKER_00"),
            SpeakerTurn(1.2, 2.0, "SPEAKER_01"),
            SpeakerTurn(2.1, 3.0, "SPEAKER_00"),
        ]

    def diarize(self, waveform: np.ndarray, sample_rate: int, min_speakers: int = 1, max_speakers: int = 10):
        return list(self.turns)


class FakeRegistry(ModelRegistry):
    """A registry whose ``load_all`` installs fakes instead of real models."""

    def __init__(self, settings, audio_llm=None, diarizer=None, text_llm=None, fail_audio=False):
        super().__init__(settings)
        self._fakes = (audio_llm or FakeAudioLLM(), diarizer or FakeDiarizer(), text_llm)
        self._fail_audio = fail_audio

    def load_all(self) -> None:
        self.device = "cpu"
        audio_llm, diarizer, text_llm = self._fakes
        if self._fail_audio:
            self.status["audio_llm"].state, self.status["audio_llm"].error = "failed", "boom"
        else:
            self.audio_llm = audio_llm
            self.status["audio_llm"].state = "ready"
        self.diarizer = diarizer
        self.status["diarization"].state = "ready"
        if text_llm is not None:
            self.text_llm = text_llm
            self.status["translation"].state = "ready"
        elif self.status["translation"].state != "disabled":
            self.status["translation"].state, self.status["translation"].error = "failed", "not configured"
