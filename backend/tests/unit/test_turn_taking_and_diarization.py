import pytest

from backend.domain.diarization import build_diarization_info, normalize_speaker_label
from backend.domain.entities import SpeakerTurn
from backend.domain.turn_taking import analyze_turn_taking, classify_style


@pytest.mark.parametrize(
    ("raw", "expected"), [("SPEAKER_00", "speaker_0"), ("speaker 12", "speaker_12"), ("Alice", "alice")]
)
def test_speaker_labels(raw, expected):
    assert normalize_speaker_label(raw) == expected


def test_statistics_and_timeline():
    turns = [
        SpeakerTurn(2.0, 3.0, "SPEAKER_01"),
        SpeakerTurn(0.0, 2.2, "SPEAKER_00"),
        SpeakerTurn(3.3, 4.0, "SPEAKER_00"),
    ]
    info = build_diarization_info(turns, total_duration=4.0)

    assert info["speakers"] == ["speaker_0", "speaker_1"]
    assert [s["start"] for s in info["segments"]] == [0.0, 2.0, 3.3]
    assert info["statistics"]["speaker_0"]["num_turns"] == 2
    assert info["statistics"]["speaker_0"]["speaking_time_percentage"] == pytest.approx(72.5)
    second, third = info["timeline"][1], info["timeline"][2]
    assert second["overlap"] is True and second["overlap_duration"] == pytest.approx(0.2)
    assert third["quick_response"] is True and third["gap"] == pytest.approx(0.3)


def test_turn_taking_metrics():
    info = build_diarization_info(
        [SpeakerTurn(0, 2, "A"), SpeakerTurn(1.5, 3, "B"), SpeakerTurn(3.1, 5, "A")], total_duration=5
    )
    metrics = analyze_turn_taking(info)
    assert metrics["num_speaker_switches"] == 2
    assert metrics["num_overlaps"] == 1
    assert metrics["num_interruptions"] == 1  # 0.5 s overlap into a 2 s turn
    assert metrics["overlap_percentage"] == 10.0


def test_turn_taking_edge_cases():
    assert analyze_turn_taking({})["turn_taking_style"] == "Unknown"
    single = build_diarization_info([SpeakerTurn(0, 1, "A")], 1)
    assert analyze_turn_taking(single)["turn_taking_style"] == "Monologue"


@pytest.mark.parametrize(
    ("overlap_pct", "avg_gap", "interruptions", "turns", "style"),
    [
        (12, 0.1, 0, 10, "Overlapping"),
        (2, 0.1, 3, 10, "Interrupted"),
        (2, 0.8, 0, 10, "Sequential"),
        (2, 0.3, 0, 10, "Smooth"),
        (2, 0.5, 0, 10, "Mixed"),  # boundary: not > 0.5 and not < 0.5
        (5, 0.3, 0, 10, "Mixed"),
    ],
)
def test_style_classification(overlap_pct, avg_gap, interruptions, turns, style):
    assert classify_style(overlap_pct, avg_gap, interruptions, turns) == style
