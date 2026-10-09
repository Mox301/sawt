"""Decode uploaded audio into the format the models expect: 16 kHz mono.

FFmpeg reads the upload from a pipe and may open nothing else, so a playlist-like
upload (ffconcat, HLS) cannot make it read server files or URLs. ``prepared_audio``
writes one temporary WAV (the audio LLM reads from a path) and loads the same
samples as a float waveform for feature extraction and diarization. The file is
removed when the context exits.
"""

import json
import logging
import os
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

import librosa
import numpy as np
from pydub import AudioSegment
from pydub.audio_segment import fix_wav_headers

from backend.core.exceptions import AudioDecodeError, PayloadTooLargeError

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16_000

# Sources up to this size decode at their native format and are resampled by pydub, as
# before; larger ones are downmixed by FFmpeg so decoded memory stays bounded.
NATIVE_MAX_CHANNELS = 2
NATIVE_MAX_RATE = 48_000

# Only the stdin pipe may be opened. ``cache:`` lets demuxers seek back (m4a with a trailing moov).
_PIPE_INPUT = ["-protocol_whitelist", "pipe,cache", "-read_ahead_limit", "-1", "-i", "cache:pipe:0"]
_STDERR_TAIL = 2000


@dataclass(frozen=True)
class PreparedAudio:
    path: str
    waveform: np.ndarray
    sample_rate: int

    @property
    def duration_s(self) -> float:
        # Millisecond resolution, matching how durations were reported before.
        return round(1000 * len(self.waveform) / self.sample_rate) / 1000.0


def decode(data: bytes, max_seconds: float) -> AudioSegment:
    """Decode any FFmpeg-readable audio of at most ``max_seconds`` into a 16 kHz mono segment."""
    probe = ["ffprobe", "-v", "error", *_PIPE_INPUT, "-show_entries", "stream=codec_type,channels,sample_rate"]
    streams = json.loads(_run([*probe, "-of", "json"], data)).get("streams", [])
    audio = [s for s in streams if s.get("codec_type") == "audio"]
    if not audio:
        raise AudioDecodeError("Could not decode audio")
    # Every audio stream is checked because FFmpeg, not the probe, picks the one it decodes.
    native = all(
        0 < s.get("channels", 0) <= NATIVE_MAX_CHANNELS and 0 < int(s.get("sample_rate", 0)) <= NATIVE_MAX_RATE
        for s in audio
    )
    downmix = [] if native else ["-ac", "1", "-ar", str(SAMPLE_RATE)]
    # Decoding stops one second past the limit, enough to tell that the audio is too long.
    ffmpeg = ["ffmpeg", "-nostdin", "-v", "error", *_PIPE_INPUT, "-vn", *downmix, "-t", str(max_seconds + 1)]
    wav = bytearray(_run([*ffmpeg, "-acodec", "pcm_s16le", "-f", "wav", "-"], data))
    fix_wav_headers(wav)  # FFmpeg cannot seek back to fill in the sizes when writing to a pipe
    segment = AudioSegment(bytes(wav))
    if segment.duration_seconds > max_seconds:
        raise PayloadTooLargeError(f"Audio longer than {max_seconds / 60:g} minutes")
    return segment.set_frame_rate(SAMPLE_RATE).set_channels(1)


def _run(command: list[str], data: bytes) -> bytes:
    result = subprocess.run(command, input=data, capture_output=True)
    if result.returncode != 0 or not result.stdout:
        stderr = result.stderr.decode(errors="replace")[-_STDERR_TAIL:]
        logger.warning("%s failed (exit %d): %s", command[0], result.returncode, stderr)
        raise AudioDecodeError("Could not decode audio")
    return result.stdout


@contextmanager
def prepared_audio(segment: AudioSegment) -> Iterator[PreparedAudio]:
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
