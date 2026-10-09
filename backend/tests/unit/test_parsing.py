import json

from backend.domain.parsing import extract_json_object, parse_conversation, parse_sentiment
from backend.tests.fakes import CONVERSATION_JSON


def test_extracts_json_from_fenced_output():
    assert extract_json_object('Here you go:\n```json\n{"a": 1}\n```') == {"a": 1}


def test_tolerates_comments_and_trailing_commas_copied_from_the_prompt():
    text = """{
      "items": [
        {"id": 1},
        {"id": 2}
        // IMPORTANT: one entry per speaker
      ],
      "url": "https://example.com/a//b",
      "quality": "Coherent",
    }"""
    assert extract_json_object(text) == {
        "items": [{"id": 1}, {"id": 2}],
        "url": "https://example.com/a//b",
        "quality": "Coherent",
    }


def test_conversation_is_normalised_to_the_full_schema():
    raw = json.loads(json.dumps(CONVERSATION_JSON))
    raw["conversation_analysis"]["overall_sentiment"] = "Ecstatic"  # not allowed
    raw["speaker_analysis"][0]["characteristic_phrases"] = "not a list"
    result = parse_conversation(json.dumps(raw))

    assert result["conversation_analysis"]["overall_sentiment"] == "Unknown"
    assert result["conversation_analysis"]["duration_estimate"] == "Unknown"
    assert result["speaker_analysis"][0]["characteristic_phrases"] == []
    assert set(result) == {
        "conversation_analysis",
        "speaker_analysis",
        "prosody_analysis",
        "interaction_analysis",
        "detailed_analysis",
    }


def test_conversation_falls_back_on_missing_sections():
    result = parse_conversation('{"conversation_analysis": {}}')
    assert "parsing_error" in result
    assert result["speaker_analysis"][0]["speaker_id"] == "Speaker 1"


def test_conversation_falls_back_without_json():
    assert parse_conversation("I cannot analyse this audio.")["parsing_error"] == "No JSON object found in response"


def test_sentiment_label_is_capitalised():
    assert parse_sentiment('{"sentiment": " negative ", "analysis": "Upset tone."}') == {
        "sentiment": "Negative",
        "analysis": "Upset tone.",
    }


def test_sentiment_fallback_reads_free_text():
    assert parse_sentiment("Overall the speaker sounds positive.")["sentiment"] == "Positive"
    assert parse_sentiment('{"sentiment": "Angry", "analysis": "x"}')["sentiment"] == "Neutral"


def test_relaxed_parsing_keeps_string_contents():
    text = '{"quote": "a, ] b, }", "list": [1, 2,], "note": "// not a comment",}'
    assert extract_json_object(text) == {"quote": "a, ] b, }", "list": [1, 2], "note": "// not a comment"}
