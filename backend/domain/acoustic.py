"""Acoustic and prosodic features of a waveform, computed with librosa.

These quantitative measurements complement the audio LLM's qualitative analysis.
Each feature group fails independently: an error in one group is reported in that
group (``{"error": ...}``) without discarding the others.
"""

import logging
from typing import Any

import librosa
import numpy as np

logger = logging.getLogger(__name__)

# Pitch tracking range (Hz) and mean-pitch categories.
PITCH_FMIN_HZ = 75
PITCH_FMAX_HZ = 400
PITCH_LOW_BELOW_HZ = 120
PITCH_MEDIUM_BELOW_HZ = 180
PITCH_MONOTONE_CV_BELOW = 0.1
PITCH_MODERATE_CV_BELOW = 0.2

# RMS energy categories and variation (std / mean).
ENERGY_LOW_BELOW = 0.02
ENERGY_MODERATE_BELOW = 0.05
ENERGY_STABLE_CV_BELOW = 0.3
ENERGY_MODERATE_CV_BELOW = 0.6

# Spectral brightness (centroid, Hz) and clarity (flatness).
CENTROID_DARK_BELOW_HZ = 1500
CENTROID_MODERATE_BELOW_HZ = 2500
FLATNESS_CLEAR_BELOW = 0.01
FLATNESS_MODERATE_BELOW = 0.05

# Speaking rate, approximated by onsets per second.
RATE_SLOW_BELOW = 3
RATE_MODERATE_BELOW = 5
SILENCE_TOP_DB = 30
MIN_PAUSE_S = 0.1

# Voice quality from mean spectral contrast.
CONTRAST_CLEAR_ABOVE = 15
CONTRAST_MODERATE_ABOVE = 10

_FEATURE_GROUPS = (
    "pitch_features",
    "energy_features",
    "spectral_features",
    "temporal_features",
    "voice_quality",
    "prosodic_statistics",
)


def extract_acoustic_features(y: np.ndarray, sr: int) -> dict[str, Any]:
    """Return all acoustic feature groups for a mono waveform."""
    try:
        return {
            "duration": librosa.get_duration(y=y, sr=sr),
            "sample_rate": sr,
            "pitch_features": _guarded(_pitch_features, y, sr),
            "energy_features": _guarded(_energy_features, y, sr),
            "spectral_features": _guarded(_spectral_features, y, sr),
            "temporal_features": _guarded(_temporal_features, y, sr),
            "voice_quality": _guarded(_voice_quality, y, sr),
            "prosodic_statistics": _guarded(_prosodic_statistics, y, sr),
        }
    except Exception as e:
        logger.error("Acoustic feature extraction failed: %s", e)
        return {"error": str(e), **{group: {} for group in _FEATURE_GROUPS}}


def _guarded(fn, y: np.ndarray, sr: int) -> dict[str, Any]:
    try:
        return fn(y, sr)
    except Exception as e:
        logger.error("%s failed: %s", fn.__name__, e)
        return {"error": str(e)}


def _pitch_features(y: np.ndarray, sr: int) -> dict[str, Any]:
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr, fmin=PITCH_FMIN_HZ, fmax=PITCH_FMAX_HZ)
    strongest = magnitudes.argmax(axis=0)
    contour = pitches[strongest, np.arange(pitches.shape[1])]
    contour = contour[contour > 0]

    if len(contour) == 0:
        return {
            "mean_pitch_hz": 0,
            "pitch_category": "Unknown",
            "pitch_variation": "Unknown",
            "pitch_range_hz": 0,
            "pitch_std_hz": 0,
        }

    mean_pitch = np.mean(contour)
    std_pitch = np.std(contour)
    min_pitch, max_pitch = np.min(contour), np.max(contour)

    if mean_pitch < PITCH_LOW_BELOW_HZ:
        category = "Low"
    elif mean_pitch < PITCH_MEDIUM_BELOW_HZ:
        category = "Medium"
    else:
        category = "High"

    cv = std_pitch / mean_pitch if mean_pitch > 0 else 0
    if cv < PITCH_MONOTONE_CV_BELOW:
        variation = "Monotone"
    elif cv < PITCH_MODERATE_CV_BELOW:
        variation = "Moderate Variation"
    else:
        variation = "High Variation"

    return {
        "mean_pitch_hz": float(mean_pitch),
        "pitch_category": category,
        "pitch_variation": variation,
        "pitch_range_hz": float(max_pitch - min_pitch),
        "min_pitch_hz": float(min_pitch),
        "max_pitch_hz": float(max_pitch),
        "pitch_std_hz": float(std_pitch),
        "coefficient_of_variation": float(cv),
    }


def _energy_features(y: np.ndarray, sr: int) -> dict[str, Any]:
    rms = librosa.feature.rms(y=y)[0]
    mean_rms, std_rms, max_rms = np.mean(rms), np.std(rms), np.max(rms)

    if mean_rms < ENERGY_LOW_BELOW:
        category = "Low"
    elif mean_rms < ENERGY_MODERATE_BELOW:
        category = "Moderate"
    else:
        category = "High"

    cv = std_rms / mean_rms if mean_rms > 0 else 0
    if cv < ENERGY_STABLE_CV_BELOW:
        variation = "Stable"
    elif cv < ENERGY_MODERATE_CV_BELOW:
        variation = "Moderate Variation"
    else:
        variation = "High Variation"

    return {
        "mean_energy": float(mean_rms),
        "energy_category": category,
        "energy_variation": variation,
        "energy_std": float(std_rms),
        "max_energy": float(max_rms),
        "dynamic_range": float(max_rms / mean_rms) if mean_rms > 0 else 0,
    }


def _spectral_features(y: np.ndarray, sr: int) -> dict[str, Any]:
    mean_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)[0])
    mean_rolloff = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr)[0])
    mean_zcr = np.mean(librosa.feature.zero_crossing_rate(y)[0])
    mean_flatness = np.mean(librosa.feature.spectral_flatness(y=y)[0])

    if mean_centroid < CENTROID_DARK_BELOW_HZ:
        brightness = "Dark/Deep"
    elif mean_centroid < CENTROID_MODERATE_BELOW_HZ:
        brightness = "Moderate"
    else:
        brightness = "Bright/Sharp"

    if mean_flatness < FLATNESS_CLEAR_BELOW:
        clarity = "Clear/Tonal"
    elif mean_flatness < FLATNESS_MODERATE_BELOW:
        clarity = "Moderate Clarity"
    else:
        clarity = "Noisy/Breathy"

    return {
        "mean_spectral_centroid_hz": float(mean_centroid),
        "brightness": brightness,
        "mean_spectral_rolloff_hz": float(mean_rolloff),
        "mean_zero_crossing_rate": float(mean_zcr),
        "mean_spectral_flatness": float(mean_flatness),
        "voice_clarity": clarity,
    }


def _temporal_features(y: np.ndarray, sr: int) -> dict[str, Any]:
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
    num_onsets = len(librosa.onset.onset_detect(y=y, sr=sr, units="time"))
    duration = librosa.get_duration(y=y, sr=sr)
    syllables_per_second = num_onsets / duration if duration > 0 else 0

    if syllables_per_second < RATE_SLOW_BELOW:
        rate = "Slow"
    elif syllables_per_second < RATE_MODERATE_BELOW:
        rate = "Moderate"
    else:
        rate = "Fast"

    intervals = librosa.effects.split(y, top_db=SILENCE_TOP_DB)
    num_pauses = len(intervals) - 1 if len(intervals) > 1 else 0
    pauses = [
        (intervals[i + 1][0] - intervals[i][1]) / sr
        for i in range(len(intervals) - 1)
        if (intervals[i + 1][0] - intervals[i][1]) / sr > MIN_PAUSE_S
    ]

    return {
        "estimated_tempo_bpm": float(np.asarray(tempo).reshape(-1)[0]),
        "syllables_per_second": float(syllables_per_second),
        "speaking_rate_category": rate,
        "num_detected_onsets": int(num_onsets),
        "num_pauses": int(num_pauses),
        "mean_pause_duration_s": float(np.mean(pauses)) if pauses else 0.0,
        "max_pause_duration_s": float(np.max(pauses)) if pauses else 0.0,
    }


def _voice_quality(y: np.ndarray, sr: int) -> dict[str, Any]:
    mean_contrast = np.mean(librosa.feature.spectral_contrast(y=y, sr=sr))

    if mean_contrast > CONTRAST_CLEAR_ABOVE:
        voice_type = "Clear/Resonant"
    elif mean_contrast > CONTRAST_MODERATE_ABOVE:
        voice_type = "Moderate Quality"
    else:
        voice_type = "Breathy/Hoarse"

    mfcc_mean = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13), axis=1)
    return {
        "voice_type": voice_type,
        "mean_spectral_contrast": float(mean_contrast),
        "mfcc_features": mfcc_mean.tolist()[:5],
    }


def _prosodic_statistics(y: np.ndarray, sr: int) -> dict[str, Any]:
    duration = librosa.get_duration(y=y, sr=sr)
    rms = librosa.feature.rms(y=y)[0]
    zcr = librosa.feature.zero_crossing_rate(y)[0]

    mean_rms = np.mean(rms)
    voiced = rms > mean_rms * 0.5
    voice_percentage = np.sum(voiced) / len(voiced) * 100
    dynamics = np.std(rms) / mean_rms if mean_rms > 0 else 0

    return {
        "total_duration_s": float(duration),
        "voice_activity_percentage": float(voice_percentage),
        "silence_percentage": float(100 - voice_percentage),
        "overall_dynamics": "High" if dynamics > 0.5 else "Low",
        "articulation_clarity": "High" if np.mean(zcr) > 0.1 else "Moderate",
    }
