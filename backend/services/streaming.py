"""Streaming sessions: audio arrives in chunks over a WebSocket and is analysed at the end.

Each chunk is an independently decodable audio segment (for example one WAV or
MP3 file per few seconds of recording). Chunks are decoded to 16 kHz mono as they
arrive and kept in memory; nothing is written to disk until analysis starts.
"""

import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Literal

from pydub import AudioSegment

from backend.core.exceptions import AudioDecodeError, PayloadTooLargeError, TooManySessionsError
from backend.infrastructure.audio_io import decode

Mode = Literal["conversation", "sentiment"]


@dataclass
class StreamSession:
    mode: Mode
    translate: bool
    max_bytes: int
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    audio: AudioSegment = field(default_factory=AudioSegment.empty)
    received_bytes: int = 0
    chunks: int = 0
    last_activity: float = field(default_factory=time.monotonic)

    def add_chunk(self, data: bytes) -> dict[str, float | int]:
        self.last_activity = time.monotonic()
        if self.received_bytes + len(data) > self.max_bytes:
            raise PayloadTooLargeError(f"Stream exceeds {self.max_bytes // (1024 * 1024)} MB")
        self.audio += decode(data)
        self.received_bytes += len(data)
        self.chunks += 1
        return {"chunk_number": self.chunks, "total_duration_s": round(self.duration_s, 3)}

    @property
    def duration_s(self) -> float:
        return len(self.audio) / 1000.0

    def finish(self) -> AudioSegment:
        if self.chunks == 0:
            raise AudioDecodeError("No audio received")
        return self.audio


class SessionLimiter:
    """Caps the number of concurrent streaming sessions."""

    def __init__(self, max_sessions: int):
        self.max_sessions = max_sessions
        self.active = 0

    @contextmanager
    def slot(self):
        if self.active >= self.max_sessions:
            raise TooManySessionsError(f"All {self.max_sessions} streaming sessions are in use")
        self.active += 1
        try:
            yield
        finally:
            self.active -= 1
