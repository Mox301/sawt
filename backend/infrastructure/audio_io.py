"""Decode uploaded audio into the format the models expect: 16 kHz mono.

``prepared_audio`` writes one temporary WAV (the audio LLM reads from a path) and
loads the same samples as a float waveform for feature extraction and diarization.
The file is removed when the context exits.
"""

import io
import logging
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

import librosa
import numpy as np
from pydub import AudioSegment

from backend.core.exceptions import AudioDecodeError

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16_000


@dataclass(frozen=True)
class PreparedAudio:
    path: str
    waveform: np.ndarray
    sample_rate: int

    @property
    def duration_s(self) -> float:
        # Millisecond resolution, matching how durations were reported before.
        return round(1000 * len(self.waveform) / self.sample_rate) / 1000.0


def decode(data: bytes) -> AudioSegment:
    """Decode any FFmpeg-readable audio into a 16 kHz mono segment."""
    try:
        segment = AudioSegment.from_file(io.BytesIO(data))
    except Exception as e:
        raise AudioDecodeError(f"Could not decode audio: {e}") from e
    return segment.set_frame_rate(SAMPLE_RATE).set_channels(1)


@contextmanager
def prepared_audio(source: bytes | AudioSegment) -> Iterator[PreparedAudio]:
    segment = source if isinstance(source, AudioSegment) else decode(source)
    if len(segment) == 0:
        raise AudioDecodeError("Audio is empty")
    fd, path = tempfile.mkstemp(suffix=".wav")
    try:
        with os.fdopen(fd, "wb") as f:
            segment.export(f, format="wav")
        waveform, sr = librosa.load(path, sr=SAMPLE_RATE)
        yield PreparedAudio(path=path, waveform=waveform, sample_rate=sr)
    finally:
        try:
            os.unlink(path)
        except OSError:
            logger.warning("Could not remove temp file %s", path)
