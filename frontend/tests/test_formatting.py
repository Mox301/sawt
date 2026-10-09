import pytest

from frontend.core.i18n import STRINGS
from frontend.utils.formatting import format_speaker_label, format_text_with_speakers, format_time, to_arabic_digits


@pytest.mark.parametrize(
    ("seconds", "english", "arabic"),
    [
        (0, "0s", "٠ث"),
        (4.25, "4.2s", "٤.٢ ث"),
        (42.5, "42.5 seconds", "٤٢.٥ ثانية"),
        (59.97, "1m", "١ د"),
        (119.97, "2m", "٢ د"),
        (120.4, "2m", "٢ د"),
        (187.0, "3m 7.0s", "٣ د ٧.٠ ث"),
        (3599.97, "1h", "١ س"),
        (3600, "1h", "١ س"),
        (3900, "1h 5m", "١ س ٥ د"),
    ],
)
def test_format_time(seconds, english, arabic):
    assert format_time(seconds, "EN") == english
    assert format_time(seconds, "AR") == arabic


def test_arabic_digits():
    assert to_arabic_digits("Room 2049") == "Room ٢٠٤٩"


def test_speaker_labels():
    assert format_speaker_label("speaker_01", "EN") == "Speaker 1"
    assert format_speaker_label("SPEAKER_12", "AR") == "متحدث ١٢"
    assert format_speaker_label("Agent", "AR") == "Agent"
    assert format_text_with_speakers("speaker_0 leads speaker_1", "AR") == "متحدث ٠ leads متحدث ١"


def test_both_languages_define_the_same_strings():
    assert STRINGS["EN"].keys() == STRINGS["AR"].keys()
