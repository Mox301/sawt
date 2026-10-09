"""Display formatting: durations, Arabic-Indic digits and speaker labels."""

import re

from frontend.core.i18n import Lang

_ARABIC_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
_SPEAKER_ID = re.compile(r"speaker[_\s]+(\d+)", re.IGNORECASE)

# (seconds suffix for < 10 s, seconds suffix for 10-60 s, minutes, hours)
_TIME_UNITS: dict[Lang, tuple[str, str, str, str]] = {
    "EN": ("s", " seconds", "m", "h"),
    "AR": (" ث", " ثانية", " د", " س"),
}


def to_arabic_digits(text: object) -> str:
    return str(text).translate(_ARABIC_DIGITS)


def _speaker_label(number: int, lang: Lang) -> str:
    return f"متحدث {to_arabic_digits(number)}" if lang == "AR" else f"Speaker {number}"


def format_speaker_label(speaker_id: str, lang: Lang = "EN") -> str:
    """``speaker_0`` → ``Speaker 0`` (EN) or ``متحدث ٠`` (AR); other ids are returned unchanged."""
    match = _SPEAKER_ID.search(speaker_id)
    return _speaker_label(int(match.group(1)), lang) if match else speaker_id


def format_text_with_speakers(text: str, lang: Lang = "EN") -> str:
    """Replace every ``speaker_N`` in free text with its display label."""
    return _SPEAKER_ID.sub(lambda m: _speaker_label(int(m.group(1)), lang), text)


def format_time(seconds: float, lang: Lang = "EN") -> str:
    """Human-readable duration, e.g. ``4.2s``, ``12.5 seconds``, ``3m 7.0s``, ``1h 5m``."""
    if seconds == 0:
        return "0s" if lang == "EN" else "٠ث"

    short_s, long_s, m, h = _TIME_UNITS[lang]
    if seconds < 60:
        text = f"{seconds:.1f}{short_s if seconds < 10 else long_s}"
    elif seconds < 3600:
        minutes, secs = int(seconds // 60), seconds % 60
        text = f"{minutes}{m}" if secs < 1 else f"{minutes}{m} {secs:.1f}{short_s}"
    else:
        hours, minutes = int(seconds // 3600), int((seconds % 3600) // 60)
        text = f"{hours}{h}" if minutes == 0 else f"{hours}{h} {minutes}{m}"
    return to_arabic_digits(text) if lang == "AR" else text
