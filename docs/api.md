# API

Interactive docs: `http://localhost:8000/docs` (OpenAPI).

## `GET /api/v1/health`

```json
{
  "status": "ready",
  "version": "1.0.0",
  "device": "mps",
  "models": {
    "audio_llm":   {"name": "mistralai/Voxtral-Mini-3B-2507", "state": "ready", "error": null},
    "diarization": {"name": "pyannote/speaker-diarization-community-1", "state": "ready", "error": null},
    "translation": {"name": "qwen3:4b-instruct-2507-q4_K_M", "state": "ready", "error": null}
  },
  "translation_available": true,
  "diarization_available": true
}
```

| `status` | Meaning |
|---|---|
| `loading` | Models are still loading |
| `ready` | Every enabled model loaded |
| `degraded` | The audio model is ready, but diarization or translation failed |
| `unavailable` | The audio model failed to load |

## `POST /api/v1/conversations/analyze`

Analyse an uploaded recording.

Multipart form fields:

| Field | Type | Default | |
|---|---|---|---|
| `audio` | file | — | Any FFmpeg-readable format (wav, mp3, m4a, flac, ogg …) |
| `translate` | bool | `false` | Also return an Arabic version |

```bash
curl -F audio=@call.wav -F translate=true http://localhost:8000/api/v1/conversations/analyze
```

The response is shortened here, and the values are illustrative; every list holds one entry per item:

```json
{
  "analysis": {
    "conversation_analysis": {
      "overall_sentiment": "Mixed",
      "main_topics": ["delayed order", "refund"],
      "conversation_summary": "…",
      "turning_points": ["…"],
      "conversation_quality": "Coherent",
      "duration_estimate": "1m 9s"
    },
    "speaker_analysis": [
      {"speaker_id": "speaker_0", "sentiment": "Negative", "speaking_style": "…", "role": "Customer",
       "emotional_state": "…", "characteristic_phrases": ["…"], "speaking_time_percentage": "45%",
       "key_contributions": "…"}
    ],
    "prosody_analysis": {
      "overall_pitch": "Medium", "overall_speaking_rate": "Moderate", "overall_energy": "Moderate",
      "tone_quality": "…", "emotional_progression": "…", "notable_acoustic_features": ["…"],
      "speaker_prosody_differences": "…",
      "prosodic_markers": {"emphasis_usage": "…", "pause_patterns": "…", "intonation_variety": "…"},
      "quantitative_metrics": {
        "pitch": {"mean_hz": 171.3, "range_hz": 310.2, "std_hz": 48.9, "category": "Medium"},
        "energy": {"mean_db": 0.041, "std_db": 0.032, "dynamic_range_db": 5.8, "category": "Moderate"},
        "speaking_rate": {"syllables_per_second": 3.9, "category": "Moderate"},
        "voice_quality": {"spectral_centroid_hz": 1720.4, "spectral_rolloff_hz": 3390.0,
                          "zero_crossing_rate": 0.09, "brightness": "Moderate", "type": "Moderate Quality"}
      }
    },
    "interaction_analysis": {
      "turn_taking_style": "Smooth", "conversational_balance": "…", "rapport_level": "Medium",
      "cooperation_vs_conflict": "…", "dominance_pattern": "…", "engagement_levels": {"speaker_0": "…"},
      "interruptions": "None", "conversation_flow": "…", "interaction_quality": "…",
      "turn_taking_details": {"num_turns": 10, "num_speaker_switches": 9, "avg_gap_between_turns_s": 0.45,
                              "transition_speed": "Moderate", "num_overlaps": 0, "overlap_percentage": 0.0,
                              "num_interruptions": 0}
    },
    "detailed_analysis": "…"
  },
  "diarization_info": {
    "speakers": ["speaker_0", "speaker_1"], "num_speakers": 2,
    "segments": [{"speaker": "speaker_0", "start": 0.03, "end": 4.1, "duration": 4.07}],
    "statistics": {"speaker_0": {"total_speaking_time": 30.2, "speaking_time_percentage": 43.4,
                                 "num_turns": 5, "average_turn_duration": 6.04}},
    "timeline": [{"turn_number": 2, "speaker": "speaker_1", "start": 4.6, "end": 9.8, "duration": 5.2,
                  "gap": 0.5}],
    "total_duration": 69.53, "diarization_method": "pyannote-community-1"
  },
  "acoustic_features": {
    "duration": 69.53, "sample_rate": 16000,
    "pitch_features": {}, "energy_features": {}, "spectral_features": {},
    "temporal_features": {}, "voice_quality": {}, "prosodic_statistics": {}
  },
  "turn_taking_metrics": {"turn_taking_style": "Smooth", "num_turns": 10, "…": "…"},
  "metadata": {"audio_filename": "call.wav", "processing_timestamp": "2026-10-09T14:03:11+00:00"}
}
```

Notes on the fields:

- `quantitative_metrics.energy.*_db` holds linear RMS amplitude. The key names are
  kept for compatibility.
- `turn_taking_metrics` and `interaction_analysis.turn_taking_details` appear only when
  the speakers switch at least once.

With `translate=true`, the response is `{"EN": <result>, "AR": <same result in Arabic>}`.
Measurements, ids and filenames are not translated. If no translation model is
available, the English result is returned with `metadata.translation = "unavailable"`.

## `WS /api/v1/conversations/stream`

Send a recording in pieces and receive the same analysis when the stream ends. Each binary frame
must be an **independently decodable audio segment**, for example one short WAV per
few seconds of recording. Frames are decoded and joined in memory.

| Direction | Message |
|---|---|
| client → | `{"type": "start", "translate": false, "filename": "live.wav"}` |
| ← server | `{"type": "started", "session_id": "…"}` |
| client → | *binary frame* (audio segment), repeated |
| ← server | `{"type": "chunk_ack", "chunk_number": 3, "total_duration_s": 15.0}` per frame |
| client → | `{"type": "end"}` |
| ← server | `{"type": "processing", "total_duration_s": 42.7}` |
| ← server | `{"type": "result", "session_id": "…", "data": { …same as the REST response… }}`, then close |
| ← server | `{"type": "error", "status": 400 \| 413 \| 422 \| 429 \| 503, "detail": "…"}`, then close |

A complete client is in [`examples/stream_client.py`](../examples/stream_client.py).

## Errors

REST errors are returned as `{"detail": "…"}`:

| Status | Meaning |
|---|---|
| 413 | Too large: the request body exceeds `SAWT_MAX_UPLOAD_MB` (rejected before it is read in full), or the recording is longer than `SAWT_MAX_AUDIO_MINUTES` |
| 422 | Not decodable audio |
| 503 | Models loading or unavailable |
