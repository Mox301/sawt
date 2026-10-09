import io

import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient

from backend.core.config import Settings
from backend.main import create_app
from backend.tests.fakes import FakeRegistry, FakeTextLLM

SR = 16_000


def tone(freq: float, seconds: float, sr: int = SR, amplitude: float = 0.3) -> np.ndarray:
    t = np.arange(int(seconds * sr)) / sr
    return (amplitude * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def wav_bytes(y: np.ndarray, sr: int = SR) -> bytes:
    buf = io.BytesIO()
    sf.write(buf, y, sr, format="WAV", subtype="PCM_16")
    return buf.getvalue()


@pytest.fixture
def dialogue_wav() -> bytes:
    """Two 'speakers' (different pitches) taking turns, with short pauses."""
    silence = np.zeros(int(0.2 * SR), dtype=np.float32)
    parts = [tone(140, 1.0), silence, tone(240, 0.8), silence, tone(140, 0.9)]
    return wav_bytes(np.concatenate(parts))


@pytest.fixture
def settings() -> Settings:
    return Settings(_env_file=None, max_upload_mb=1, stream_idle_timeout_s=5, stream_max_sessions=2)


@pytest.fixture
def make_client(settings):
    clients = []

    def _make(**registry_kwargs) -> TestClient:
        registry = FakeRegistry(settings, **registry_kwargs)
        client = TestClient(create_app(settings, registry, load_in_background=False))
        client.__enter__()
        clients.append(client)
        return client

    yield _make
    for c in clients:
        c.__exit__(None, None, None)


@pytest.fixture
def client(make_client) -> TestClient:
    return make_client(text_llm=FakeTextLLM())
