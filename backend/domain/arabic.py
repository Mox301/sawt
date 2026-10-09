"""Arabic-specific text handling: glossary, digits and speaker labels.

``GLOSSARY`` holds fixed EN→AR translations for the categorical values the
analysis produces (sentiment, roles, pitch levels …). Using fixed terms keeps
labels consistent across results; only free-text fields go to the translation
model.
"""

import re

# Keys whose values are never translated (numbers, ids, raw measurements).
NON_TRANSLATABLE_KEYS = frozenset(
    {
        "speaking_time_percentage",
        "mean_hz",
        "range_hz",
        "std_hz",
        "mean_db",
        "std_db",
        "syllables_per_second",
        "spectral_centroid_hz",
        "spectral_rolloff_hz",
        "zero_crossing_rate",
        "audio_filename",
        "processing_timestamp",
        "diarization_info",
        "acoustic_features",
        "metadata",
    }
)

GLOSSARY: dict[str, str] = {
    # Sentiment values
    "Positive": "إيجابي",
    "Negative": "سلبي",
    "Neutral": "محايد",
    "Mixed": "مختلط",
    # Conversation quality
    "Coherent": "متماسك",
    "Somewhat Coherent": "متماسك نوعاً ما",
    "Fragmented": "متقطع",
    # Speaking style descriptors
    "Formal": "رسمي",
    "Informal": "غير رسمي",
    "Assertive": "واثق من نفسه",
    "Passive": "متحفظ",
    "Calm": "هادئ",
    "Emotional": "عاطفي",
    "Confident": "واثق",
    "Hesitant": "متردد",
    # Speaker roles
    "Initiator": "بادئ الحوار",
    "Responder": "المجيب",
    "Facilitator": "المنسق",
    "Narrator": "الراوي",
    "Interviewer": "المحاور",
    "Interviewee": "الضيف",
    "Debater": "المناظر",
    "Announcer": "المذيع",
    "Presenter": "المقدم",
    "Guest": "الضيف",
    # Pitch patterns
    "High": "عالية",
    "Medium": "متوسطة",
    "Low": "منخفضة",
    "Variable": "متغيرة",
    "Monotone": "رتيبة",
    "Varied": "متنوعة",
    # Speaking rate
    "Fast": "سريع",
    "Moderate": "معتدل",
    "Slow": "بطيء",
    "Very Fast": "سريع جداً",
    "Very Slow": "بطيء جداً",
    # Volume/Energy
    "Loud": "عالي",
    "Soft": "هادئ",
    "Varying intensity": "متغير الشدة",
    "High energy": "حيوي",
    "Low energy": "هادئ",
    # Tone quality
    "Warm": "ودود",
    "Cold": "جاف",
    "Tense": "متوتر",
    "Relaxed": "مسترخي",
    "Professional": "محترف",
    "Casual": "عادي",
    "Friendly": "ودي",
    # Voice characteristics
    "Clear": "واضح",
    "Hoarse": "صوت خشن",
    "Breathy": "صوت ناعم",
    "Resonant": "صوت قوي",
    "Strong": "قوي",
    "Weak": "ضعيف",
    # Additional values
    "Clear/Resonant": "واضح ورنان",
    "Dark/Deep": "عميق",
    "Not Applicable": "غير متاح",
    "Unknown": "غير معروف",
    "N/A": "غير متاح",
    # Turn-taking terms
    "Frequent": "متكرر",
    "Occasional": "أحياناً",
    "Rare": "نادر",
    "Overlapping": "متداخل",
    "Interruptions": "مقاطعات",
    "Smooth transitions": "انتقالات سلسة",
}

ARABIC_INDIC_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
SPEAKER_WORD_AR = "متحدث"

_ARABIC_CHARS = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")
_SPEAKER_REF = re.compile(r"(Speaker|SPEAKER|speaker)[_\s]+(\d+)", re.IGNORECASE)
_SPEAKER_ID = re.compile(r"^(Speaker|SPEAKER|speaker)[_\s]\d+$", re.IGNORECASE)
_DOMINATED_BY = re.compile(r"Dominated by (Speaker|SPEAKER)[_\s]+(\d+)", re.IGNORECASE)
_SENTENCE_MARKERS = (
    " the ",
    " is ",
    " are ",
    " was ",
    " were ",
    " has ",
    " have ",
    " and ",
    " but ",
    " with ",
    " from ",
    " about ",
    " between ",
)
MAX_GLOSSARY_WORDS = 4


def is_arabic(text: str) -> bool:
    return bool(text) and bool(_ARABIC_CHARS.search(text))


def to_arabic_digits(number: str) -> str:
    return number.translate(ARABIC_INDIC_DIGITS)


def is_speaker_id(text: str) -> bool:
    return bool(_SPEAKER_ID.match(text))


def replace_speaker_refs(text: str) -> str:
    """``Speaker 1`` / ``speaker_1`` → ``متحدث ١``."""
    if not text:
        return text
    return _SPEAKER_REF.sub(lambda m: f"{SPEAKER_WORD_AR} {to_arabic_digits(m.group(2))}", text)


def mask_speaker_refs(text: str) -> tuple[str, dict[str, str]]:
    """Replace speaker references with ``__SPK_n__`` placeholders the translator keeps intact."""
    placeholders: dict[str, str] = {}

    def _mask(match: re.Match) -> str:
        key = f"__SPK_{len(placeholders)}__"
        placeholders[key] = match.group(0)
        return key

    return _SPEAKER_REF.sub(_mask, text), placeholders


def unmask_speaker_refs(text: str, placeholders: dict[str, str]) -> str:
    for key, original in placeholders.items():
        replacement = replace_speaker_refs(original)
        text = text.replace(key, replacement)
        bare = key.replace("_", "")  # models sometimes drop the underscores
        if bare in text:
            text = text.replace(bare, replacement)
    return replace_speaker_refs(text)


def glossary_lookup(text: str) -> str | None:
    """Fixed translation for short categorical values; ``None`` for free text."""
    text = text.strip()
    if len(text.split()) > MAX_GLOSSARY_WORDS or any(m in text.lower() for m in _SENTENCE_MARKERS):
        return None
    if text in GLOSSARY:
        return GLOSSARY[text]
    match = _DOMINATED_BY.match(text)
    if match:
        return f"يهيمن عليه {SPEAKER_WORD_AR} {to_arabic_digits(match.group(2))}"
    return None
