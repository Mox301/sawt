import pytest

from backend.core.exceptions import AudioDecodeError, PayloadTooLargeError
from backend.infrastructure.audio_io import SAMPLE_RATE, prepared_audio
from backend.services.streaming import SessionLimiter, StreamSession
from backend.tests.conftest import tone, wav_bytes


def test_prepared_audio_resamples_and_cleans_up():
    stereo_44k = wav_bytes(tone(200, 1.0, sr=44_100), sr=44_100)
    with prepared_audio(stereo_44k) as audio:
        path = audio.path
        assert audio.sample_rate == SAMPLE_RATE
        assert audio.duration_s == pytest.approx(1.0, abs=0.01)
    import os

    assert not os.path.exists(path)


def test_undecodable_audio():
    with pytest.raises(AudioDecodeError), prepared_audio(b"not audio at all"):
        pass


def test_stream_session_accumulates_chunks():
    session = StreamSession(translate=False, max_bytes=10_000_000)
    session.add_chunk(wav_bytes(tone(200, 0.5)))
    ack = session.add_chunk(wav_bytes(tone(300, 0.25)))
    assert ack == {"chunk_number": 2, "total_duration_s": 0.75}


def test_stream_session_limits():
    session = StreamSession(translate=False, max_bytes=100)
    with pytest.raises(PayloadTooLargeError):
        session.add_chunk(wav_bytes(tone(200, 0.5)))
    with pytest.raises(AudioDecodeError):
        session.finish()


def test_session_limiter():
    limiter = SessionLimiter(1)
    with limiter.slot(), pytest.raises(Exception, match="in use"), limiter.slot():
        pass
    with limiter.slot():
        assert limiter.active == 1
