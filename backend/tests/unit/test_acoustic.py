import numpy as np
import pytest

from backend.domain.acoustic import extract_acoustic_features
from backend.tests.conftest import SR, tone


def test_pitch_of_a_pure_tone():
    features = extract_acoustic_features(tone(220, 2.0), SR)
    pitch = features["pitch_features"]
    assert pitch["mean_pitch_hz"] == pytest.approx(220, rel=0.05)
    assert pitch["pitch_category"] == "High"
    assert features["duration"] == pytest.approx(2.0)


def test_all_feature_groups_present():
    features = extract_acoustic_features(tone(150, 1.5), SR)
    for group in (
        "pitch_features",
        "energy_features",
        "spectral_features",
        "temporal_features",
        "voice_quality",
        "prosodic_statistics",
    ):
        assert group in features and "error" not in features[group], group
    assert features["energy_features"]["dynamic_range"] > 0
    assert features["spectral_features"]["mean_spectral_centroid_hz"] > 0


def test_silence_has_unknown_pitch():
    features = extract_acoustic_features(np.zeros(SR, dtype=np.float32), SR)
    assert features["pitch_features"]["pitch_category"] == "Unknown"
