"""pyannote speaker-diarization adapter (``Diarizer``)."""

import logging

import numpy as np
import torch
from pyannote.audio import Pipeline

from backend.domain.entities import SpeakerTurn

logger = logging.getLogger(__name__)


class PyannoteDiarizer:
    def __init__(self, model_id: str, device: str, token: str | None = None):
        # token=None lets huggingface_hub use the token stored by `hf auth login`.
        self.pipeline = Pipeline.from_pretrained(model_id, token=token)
        if self.pipeline is None:
            raise RuntimeError(f"Could not load {model_id}; accept its terms on Hugging Face and log in")
        self.pipeline.to(torch.device(device))
        logger.info("Diarization pipeline loaded on %s", device)

    def diarize(
        self, waveform: np.ndarray, sample_rate: int, min_speakers: int = 1, max_speakers: int = 10
    ) -> list[SpeakerTurn]:
        # Pass audio in memory so pyannote does not need its own decoder (torchcodec/FFmpeg).
        audio = {"waveform": torch.from_numpy(waveform).float().unsqueeze(0), "sample_rate": sample_rate}
        output = self.pipeline(audio, min_speakers=min_speakers, max_speakers=max_speakers)
        annotation = getattr(output, "speaker_diarization", output)
        return [
            SpeakerTurn(segment.start, segment.end, label)
            for segment, _, label in annotation.itertracks(yield_label=True)
        ]
