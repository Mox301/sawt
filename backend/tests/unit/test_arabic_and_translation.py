import hashlib

from backend.domain.arabic import glossary_lookup, is_arabic, mask_speaker_refs, replace_speaker_refs, to_arabic_digits
from backend.prompts.conversation import CONVERSATION_ANALYSIS_PROMPT
from backend.services.translation import TranslationService
from backend.tests.fakes import FakeTextLLM


def test_prompt_is_unchanged():
    """The prompt is tuned; any edit must be deliberate (update the hash with it)."""
    assert hashlib.sha256(CONVERSATION_ANALYSIS_PROMPT.encode()).hexdigest()[:16] == "94a38a94ed357642"


def test_arabic_helpers():
    assert to_arabic_digits("2025") == "٢٠٢٥"
    assert replace_speaker_refs("speaker_0 then Speaker 11") == "متحدث ٠ then متحدث ١١"
    assert is_arabic("مرحبا") and not is_arabic("hello")
    assert glossary_lookup("Positive") == "إيجابي"
    assert glossary_lookup("Dominated by Speaker 2") == "يهيمن عليه متحدث ٢"
    assert glossary_lookup("The speaker is calm") is None  # sentences go to the model
    masked, placeholders = mask_speaker_refs("Speaker 1 interrupts speaker_2")
    assert masked == "__SPK_0__ interrupts __SPK_1__"
    assert placeholders == {"__SPK_0__": "Speaker 1", "__SPK_1__": "speaker_2"}


def _result():
    return {
        "analysis": {
            "conversation_analysis": {
                "overall_sentiment": "Positive",
                "conversation_summary": "Speaker 1 helps the caller.",
            },
            "speaker_analysis": [{"speaker_id": "speaker_0", "speaking_time_percentage": "45%", "role": "Agent"}],
        },
        "acoustic_features": {"pitch_features": {"pitch_category": "High"}},
        "metadata": {"audio_filename": "call.wav"},
        "turn_taking_metrics": {"turn_taking_style": "Smooth", "num_turns": 4},
    }


def test_bilingual_translation():
    llm = FakeTextLLM()
    out = TranslationService(llm).translate(_result())
    ar = out["AR"]

    assert out["EN"] == _result()
    assert ar["analysis"]["conversation_analysis"]["overall_sentiment"] == "إيجابي"  # glossary
    assert ar["analysis"]["speaker_analysis"][0]["speaker_id"] == "متحدث ٠"  # speaker id rule
    assert ar["analysis"]["speaker_analysis"][0]["speaking_time_percentage"] == "45%"  # non-translatable
    assert ar["acoustic_features"] == _result()["acoustic_features"]  # measurements untouched
    # Free text goes to the model with speaker refs masked, and comes back unmasked in Arabic.
    assert ar["analysis"]["conversation_analysis"]["conversation_summary"] == "ترجمة[متحدث ١ helps the caller.]"
    assert any("__SPK_0__ helps the caller." in p for p in llm.prompts)
    assert len(llm.prompts) == 2  # summary and "Agent"; "Smooth" comes from the glossary
    assert ar["turn_taking_metrics"]["turn_taking_style"] == "سلس"


def test_empty_model_output_keeps_english():
    class Silent(FakeTextLLM):
        def generate_batch(self, prompts, max_new_tokens):
            return [""] * len(prompts)

    ar = TranslationService(Silent()).translate(_result())["AR"]
    assert ar["analysis"]["conversation_analysis"]["conversation_summary"] == "Speaker 1 helps the caller."


def test_without_text_model_result_is_marked():
    out = TranslationService(None).translate(_result())
    assert "EN" not in out
    assert out["metadata"] == {"audio_filename": "call.wav", "translation": "unavailable"}


def test_invented_placeholder_falls_back_to_english():
    """Small models sometimes echo the prompt's __SPK_0__ example instead of translating."""

    class Echo(FakeTextLLM):
        def generate_batch(self, prompts, max_new_tokens):
            return ["__SPK_0__"] * len(prompts)

    data = {"analysis": {"note": "Quite brief exchange", "interruptions": "None"}}
    ar = TranslationService(Echo()).translate(data)["AR"]["analysis"]
    assert ar["note"] == "Quite brief exchange"
    assert ar["interruptions"] == "لا يوجد"  # deterministic label, never sent to the model
