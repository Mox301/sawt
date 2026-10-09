from datetime import datetime

from frontend.services.report import build_report

GENERATED_AT = datetime(2026, 10, 9, 12, 0, 0)


def test_report_is_english_and_complete(bilingual_response):
    report = build_report(bilingual_response, "call.wav", GENERATED_AT)

    assert report.startswith("SAWT CONVERSATION ANALYSIS REPORT\nGenerated: 2026-10-09 12:00:00\nFile: call.wav")
    assert "Actual Duration: 42.5 seconds" in report
    for section in (
        "CONVERSATION OVERVIEW",
        "SPEAKER DIARIZATION STATISTICS",
        "INDIVIDUAL SPEAKER ANALYSIS",
        "PROSODY & ACOUSTIC ANALYSIS",
        "INTERACTION DYNAMICS",
        "DETAILED ANALYSIS",
        "END OF REPORT",
    ):
        assert section in report
    assert "Overall Sentiment: Mixed" in report
    assert "مختلط" not in report
    assert "Speaker 1:" in report
    assert "Syllables/Second: 4.12" in report
    assert "words_per_minute" not in report.lower()


def test_single_speaker_report_skips_interaction(english_result):
    diarization = english_result["diarization_info"]
    diarization.update(speakers=["speaker_0"], num_speakers=1)
    diarization["statistics"].pop("speaker_1")

    report = build_report(english_result, "solo.wav", GENERATED_AT)

    assert "INTERACTION DYNAMICS" not in report
    assert "Number of Speakers: 1" in report
