from frontend.services.result_parser import NO_DETAILED_ANALYSIS, is_bilingual, parse_result


def test_bilingual_response_picks_the_requested_language(bilingual_response):
    assert is_bilingual(bilingual_response)

    english = parse_result(bilingual_response, "EN")
    arabic = parse_result(bilingual_response, "AR")

    assert english.conversation["overall_sentiment"] == "Mixed"
    assert arabic.conversation["overall_sentiment"] == "مختلط"
    assert arabic.conversation["main_topics"] == ["الفواتير", "انقطاع الخدمة"]
    assert arabic.detailed_analysis == "مكالمة دعم قصيرة تنتهي بشكل ودي."
    assert [s["speaker_id"] for s in arabic.speakers] == ["speaker_0", "speaker_1"]
    assert arabic.num_speakers == 2
    assert arabic.duration_s == 42.5


def test_single_language_response_serves_english_content_to_both_languages(untranslated_response):
    assert not is_bilingual(untranslated_response)

    english = parse_result(untranslated_response, "EN")
    arabic = parse_result(untranslated_response, "AR")

    assert arabic == english
    assert arabic.conversation["overall_sentiment"] == "Mixed"
    assert arabic.prosody["quantitative_metrics"]["speaking_rate"]["syllables_per_second"] == 4.12
    assert arabic.interaction["turn_taking_details"]["num_turns"] == 6
    assert arabic.diarization["statistics"]["speaker_1"]["num_turns"] == 2


def test_placeholder_detailed_analysis_is_dropped(english_result):
    english_result["analysis"]["detailed_analysis"] = NO_DETAILED_ANALYSIS
    assert parse_result(english_result, "EN").detailed_analysis == ""


def test_duration_falls_back_to_diarization_then_none(english_result):
    del english_result["acoustic_features"]["duration"]
    english_result["diarization_info"]["total_duration"] = 40.0
    assert parse_result(english_result, "EN").duration_s == 40.0

    english_result["diarization_info"] = {"error": "Diarization model not loaded", "note": "Diarization unavailable"}
    view = parse_result(english_result, "EN")
    assert view.duration_s is None
    assert view.num_speakers == 1


def test_empty_response_yields_empty_sections():
    view = parse_result({}, "AR")
    assert (view.conversation, view.speakers, view.prosody, view.interaction) == ({}, [], {}, {})
    assert view.detailed_analysis == ""
