import copy

from backend.domain.prosody import add_acoustic_metrics, apply_turn_taking, format_duration, override_duration
from backend.tests.fakes import CONVERSATION_JSON

ACOUSTIC = {
    "duration": 75.4,
    "pitch_features": {"mean_pitch_hz": 182.5, "pitch_range_hz": 120.0, "pitch_std_hz": 30.1, "pitch_category": "High"},
    "energy_features": {"mean_energy": 0.04, "energy_std": 0.02, "dynamic_range": 6.5, "energy_category": "Moderate"},
    "spectral_features": {
        "mean_spectral_centroid_hz": 1800.0,
        "mean_spectral_rolloff_hz": 3500.0,
        "mean_zero_crossing_rate": 0.08,
        "brightness": "Moderate",
    },
    "temporal_features": {"syllables_per_second": 4.2, "speaking_rate_category": "Moderate"},
    "voice_quality": {"voice_type": "Moderate Quality"},
}


def _analysis():
    return copy.deepcopy(CONVERSATION_JSON)


def test_quantitative_metrics_read_the_real_feature_keys():
    """Regression: dynamic range, spectral centroid/rolloff and ZCR used to be always 0."""
    result, analysis = {"acoustic_features": ACOUSTIC}, _analysis()
    add_acoustic_metrics(result, analysis)
    m = analysis["prosody_analysis"]["quantitative_metrics"]

    assert m["energy"]["dynamic_range_db"] == 6.5
    assert m["voice_quality"]["spectral_centroid_hz"] == 1800.0
    assert m["voice_quality"]["spectral_rolloff_hz"] == 3500.0
    assert m["voice_quality"]["zero_crossing_rate"] == 0.08
    assert m["pitch"]["mean_hz"] == 182.5
    assert "estimated_words_per_minute" not in m["speaking_rate"]


def test_unknown_categories_are_filled_from_measurements_only():
    result, analysis = {"acoustic_features": ACOUSTIC}, _analysis()
    add_acoustic_metrics(result, analysis)
    prosody = analysis["prosody_analysis"]
    assert prosody["overall_pitch"] == "High"  # was Unknown
    assert prosody["overall_energy"] == "Moderate"  # was Unknown
    assert prosody["overall_speaking_rate"] == "Moderate"  # model's own value kept


def test_no_metrics_without_features():
    analysis = _analysis()
    add_acoustic_metrics({"acoustic_features": {"error": "x"}}, analysis)
    assert "quantitative_metrics" not in analysis["prosody_analysis"]


def test_duration_formatting_and_override():
    assert format_duration(42.04) == "42.0 seconds"
    assert format_duration(75.4) == "1m 15s"
    assert format_duration(3725) == "1h 2m"
    analysis = _analysis()
    override_duration({"acoustic_features": ACOUSTIC}, analysis)
    assert analysis["conversation_analysis"]["duration_estimate"] == "1m 15s"


def test_turn_taking_overrides_llm_guesses():
    result, analysis = {}, _analysis()
    metrics = {"num_speaker_switches": 3, "num_turns": 10, "num_interruptions": 2, "turn_taking_style": "Overlapping"}
    apply_turn_taking(result, analysis, metrics)
    interaction = analysis["interaction_analysis"]
    assert result["turn_taking_metrics"] is metrics
    assert interaction["turn_taking_style"] == "Overlapping"
    assert interaction["interruptions"] == "Occasional"
    assert interaction["turn_taking_details"]["num_turns"] == 10


def test_no_speaker_switches_removes_turn_taking_fields():
    result, analysis = {}, _analysis()
    apply_turn_taking(result, analysis, {"num_speaker_switches": 0})
    assert "turn_taking_metrics" not in result
    assert "turn_taking_style" not in analysis["interaction_analysis"]
    assert analysis["interaction_analysis"]["interruptions"] == "Not Applicable (No speaker switches)"
