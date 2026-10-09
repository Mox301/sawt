"""Plain-text report of an analysis result (always in English)."""

from datetime import datetime
from typing import Any

from frontend.services.result_parser import ResultView, parse_result
from frontend.utils.formatting import format_speaker_label, format_time

RULE = "=" * 80


def build_report(data: dict[str, Any], file_name: str, generated_at: datetime | None = None) -> str:
    view = parse_result(data, "EN")
    sections = [
        _header(view, file_name, generated_at or datetime.now()),
        _overview(view.conversation),
        _diarization(view.diarization),
        _speakers(view.speakers),
        _prosody(view.prosody),
        _interaction(view.interaction) if view.num_speakers > 1 else "",
        _section("DETAILED ANALYSIS", [view.detailed_analysis]) if view.detailed_analysis else "",
        f"{RULE}\nEND OF REPORT\n{RULE}",
    ]
    return "\n\n".join(s for s in sections if s)


def _section(title: str, lines: list[str]) -> str:
    return "\n".join([RULE, title, RULE, *lines])


def _header(view: ResultView, file_name: str, generated_at: datetime) -> str:
    duration = format_time(view.duration_s) if view.duration_s else "Unknown"
    return (
        "SAWT CONVERSATION ANALYSIS REPORT\n"
        f"Generated: {generated_at:%Y-%m-%d %H:%M:%S}\n"
        f"File: {file_name}\n"
        f"Actual Duration: {duration}"
    )


def _overview(conv: dict[str, Any]) -> str:
    topics = conv.get("main_topics", [])
    lines = [
        f"Overall Sentiment: {conv.get('overall_sentiment', 'N/A')}",
        f"Quality: {conv.get('conversation_quality', 'N/A')}",
        f"Duration: {conv.get('duration_estimate', 'N/A')}",
        "",
        "Main Topics:",
        *([f"  • {topic}" for topic in topics] or ["  N/A"]),
        "",
        "Summary:",
        conv.get("conversation_summary", "N/A"),
    ]
    if turning_points := conv.get("turning_points", []):
        lines += ["", "Key Moments:", *(f"  {i}. {point}" for i, point in enumerate(turning_points, 1))]
    return _section("CONVERSATION OVERVIEW", lines)


def _diarization(diarization: dict[str, Any]) -> str:
    if "statistics" not in diarization:
        return ""
    lines = [
        f"Number of Speakers: {diarization.get('num_speakers', 0)}",
        f"Total Audio Duration: {diarization.get('total_duration', 0):.2f}s",
        f"Diarization Method: {diarization.get('diarization_method', 'N/A')}",
        "",
    ]
    for speaker, stat in diarization["statistics"].items():
        share = stat.get("speaking_time_percentage", 0)
        lines += [
            f"{format_speaker_label(speaker)}:",
            f"  Speaking Time: {stat.get('total_speaking_time', 0):.2f}s ({share:.1f}%)",
            f"  Number of Turns: {stat.get('num_turns', 0)}",
            f"  Average Turn Duration: {stat.get('average_turn_duration', 0):.2f}s",
            "",
        ]
    return _section("SPEAKER DIARIZATION STATISTICS", lines)


def _speakers(speakers: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for speaker in speakers:
        lines += [
            "",
            f"{format_speaker_label(speaker.get('speaker_id', 'Unknown'))}:",
            f"  Sentiment: {speaker.get('sentiment', 'N/A')}",
            f"  Role: {speaker.get('role', 'N/A')}",
            f"  Speaking Style: {speaker.get('speaking_style', 'N/A')}",
            f"  Emotional State: {speaker.get('emotional_state', 'N/A')}",
            f"  Speaking Time: {speaker.get('speaking_time_percentage', 'N/A')}",
        ]
        contributions = speaker.get("key_contributions", "")
        if contributions and contributions != "Not specified":
            lines.append(f"  Key Contributions: {contributions}")
        if phrases := speaker.get("characteristic_phrases", []):
            lines += ["  Characteristic Phrases:", *(f"    - {phrase}" for phrase in phrases)]
    return _section("INDIVIDUAL SPEAKER ANALYSIS", lines)


def _prosody(prosody: dict[str, Any]) -> str:
    if not prosody:
        return ""
    lines = [
        f"Overall Pitch: {prosody.get('overall_pitch', 'N/A')}",
        f"Speaking Rate: {prosody.get('overall_speaking_rate', 'N/A')}",
        f"Energy Level: {prosody.get('overall_energy', 'N/A')}",
        f"Tone Quality: {prosody.get('tone_quality', 'N/A')}",
    ]
    if metrics := prosody.get("quantitative_metrics"):
        lines += ["", "Quantitative Measurements:", *_quantitative_metrics(metrics)]
    return _section("PROSODY & ACOUSTIC ANALYSIS", lines)


def _quantitative_metrics(metrics: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    if pitch := metrics.get("pitch"):
        lines += [
            "  Pitch:",
            f"    Mean: {pitch.get('mean_hz', 0):.1f} Hz",
            f"    Range: {pitch.get('range_hz', 0):.1f} Hz",
            f"    Category: {pitch.get('category', 'N/A')}",
        ]
    if rate := metrics.get("speaking_rate"):
        lines += [
            "  Speaking Rate:",
            f"    Syllables/Second: {rate.get('syllables_per_second', 0):.2f}",
            f"    Category: {rate.get('category', 'N/A')}",
        ]
    if voice := metrics.get("voice_quality"):
        lines += [
            "  Voice Quality:",
            f"    Type: {voice.get('type', 'N/A')}",
            f"    Brightness: {voice.get('brightness', 'N/A')}",
        ]
    return lines


def _interaction(interaction: dict[str, Any]) -> str:
    if not interaction:
        return ""
    lines = [
        f"Conversational Balance: {interaction.get('conversational_balance', 'N/A')}",
        f"Turn-Taking Style: {interaction.get('turn_taking_style', 'N/A')}",
        f"Interruptions: {interaction.get('interruptions', 'N/A')}",
        f"Rapport Level: {interaction.get('rapport_level', 'N/A')}",
        f"Cooperation vs Conflict: {interaction.get('cooperation_vs_conflict', 'N/A')}",
    ]
    if details := interaction.get("turn_taking_details"):
        lines += [
            "",
            "Turn-Taking Details:",
            f"  Total Turns: {details.get('num_turns', 0)}",
            f"  Speaker Switches: {details.get('num_speaker_switches', 0)}",
            f"  Average Gap: {details.get('avg_gap_between_turns_s', 0):.2f}s",
            f"  Overlaps: {details.get('num_overlaps', 0)} ({details.get('overlap_percentage', 0):.1f}%)",
            f"  Interruptions: {details.get('num_interruptions', 0)}",
            f"  Transition Speed: {details.get('transition_speed', 'N/A')}",
        ]
    dominance = interaction.get("dominance_pattern", "")
    if dominance and dominance != "Not described":
        lines += ["", "Dominance Pattern:", dominance]
    if engagement := interaction.get("engagement_levels", {}):
        lines += ["", "Engagement Levels:", *(f"  {format_speaker_label(s)}: {lvl}" for s, lvl in engagement.items())]
    return _section("INTERACTION DYNAMICS", lines)
