import io
import os
import subprocess

import numpy as np
import pytest
from pydub import AudioSegment

from backend.core.exceptions import AudioDecodeError, PayloadTooLargeError
from backend.infrastructure.audio_io import SAMPLE_RATE, decode, prepared_audio
from backend.services.streaming import SessionLimiter, StreamSession
from backend.tests.conftest import tone, wav_bytes

LIMIT_S = 60


def stereo(seconds: float, sr: int) -> np.ndarray:
    return np.stack([tone(200, seconds, sr=sr), tone(300, seconds, sr=sr)], axis=1)


def test_prepared_audio_resamples_and_cleans_up():
    with prepared_audio(decode(wav_bytes(stereo(1.0, 44_100), sr=44_100), LIMIT_S)) as audio:
        path = audio.path
        assert audio.sample_rate == SAMPLE_RATE
        assert audio.duration_s == pytest.approx(1.0, abs=0.01)
    assert not os.path.exists(path)


@pytest.mark.parametrize(
    "wav", [wav_bytes(stereo(1.3, 44_100), sr=44_100), wav_bytes(tone(200, 1.3))], ids=["44k-stereo", "16k-mono"]
)
def test_decode_matches_the_previous_pydub_pipeline(wav):
    before = AudioSegment.from_file(io.BytesIO(wav)).set_frame_rate(SAMPLE_RATE).set_channels(1)
    after = decode(wav, LIMIT_S)
    assert (after.frame_rate, after.channels, after.sample_width) == (SAMPLE_RATE, 1, 2)
    assert np.array_equal(np.array(after.get_array_of_samples()), np.array(before.get_array_of_samples()))


def test_decode_downmixes_many_channels_and_high_rates_in_ffmpeg(monkeypatch):
    commands = []
    run = subprocess.run

    def spy(command, **kwargs):
        commands.append(command)
        return run(command, **kwargs)

    monkeypatch.setattr(subprocess, "run", spy)

    decode(wav_bytes(tone(200, 0.5)), LIMIT_S)
    assert "-ac" not in commands[-1] and "-ar" not in commands[-1]

    six_channels_96k = np.stack([tone(200, 1.0, sr=96_000)] * 6, axis=1)
    segment = decode(wav_bytes(six_channels_96k, sr=96_000), LIMIT_S)
    ffmpeg = commands[-1]
    assert ffmpeg[ffmpeg.index("-ac") + 1] == "1" and ffmpeg[ffmpeg.index("-ar") + 1] == str(SAMPLE_RATE)
    assert (segment.frame_rate, segment.channels) == (SAMPLE_RATE, 1)
    assert segment.duration_seconds == pytest.approx(1.0, abs=0.01)


def test_decode_reads_m4a_with_the_index_at_the_end(tmp_path):
    source, m4a = tmp_path / "a.wav", tmp_path / "a.m4a"
    source.write_bytes(wav_bytes(tone(200, 1.0)))
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(source), "-c:a", "aac", str(m4a)], check=True)
    assert decode(m4a.read_bytes(), LIMIT_S).duration_seconds == pytest.approx(1.0, abs=0.05)


def test_decode_refuses_playlists_that_reference_local_files(tmp_path, monkeypatch):
    (tmp_path / "secret.wav").write_bytes(wav_bytes(tone(200, 1.0)))
    monkeypatch.chdir(tmp_path)  # FFmpeg resolves the relative path against the working directory
    with pytest.raises(AudioDecodeError) as error:
        decode(b"ffconcat version 1.0\nfile secret.wav\n", LIMIT_S)
    assert str(error.value) == "Could not decode audio"


def test_decode_rejects_audio_over_the_limit():
    with pytest.raises(PayloadTooLargeError, match="Audio longer than 0.05 minutes"):
        decode(wav_bytes(tone(200, 3.5)), 3)


def test_undecodable_audio():
    with pytest.raises(AudioDecodeError, match="^Could not decode audio$"):
        decode(b"not audio at all", LIMIT_S)


def test_stream_session_accumulates_chunks():
    session = StreamSession(translate=False, max_bytes=10_000_000, max_seconds=LIMIT_S)
    session.add_chunk(wav_bytes(tone(200, 0.5)))
    ack = session.add_chunk(wav_bytes(tone(300, 0.25)))
    assert ack == {"chunk_number": 2, "total_duration_s": 0.75}


def test_stream_session_limits():
    session = StreamSession(translate=False, max_bytes=100, max_seconds=LIMIT_S)
    with pytest.raises(PayloadTooLargeError):
        session.add_chunk(wav_bytes(tone(200, 0.5)))
    with pytest.raises(AudioDecodeError):
        session.finish()


def test_stream_session_limits_the_total_duration():
    session = StreamSession(translate=False, max_bytes=10_000_000, max_seconds=1)
    session.add_chunk(wav_bytes(tone(200, 0.75)))
    with pytest.raises(PayloadTooLargeError, match="Audio longer than"):
        session.add_chunk(wav_bytes(tone(200, 0.5)))
    assert session.duration_s == 0.75


def test_session_limiter():
    limiter = SessionLimiter(1)
    with limiter.slot(), pytest.raises(Exception, match="in use"), limiter.slot():
        pass
    with limiter.slot():
        assert limiter.active == 1


def test_stream_duration_limit_reports_the_session_limit():
    session = StreamSession(translate=False, max_bytes=10_000_000, max_seconds=1)
    session.add_chunk(wav_bytes(tone(200, 0.8)))
    with pytest.raises(PayloadTooLargeError, match="longer than 0.0166667 minutes"):
        session.add_chunk(wav_bytes(tone(200, 0.8)))
