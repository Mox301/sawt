# Changelog

## 1.0.0 — 2026-10-09

First public release.

- Multi-speaker conversation analysis: Voxtral-Mini-3B audio-LLM analysis, pyannote
  diarization, librosa prosody features and turn-taking metrics in one result.
- Sentiment analysis endpoint.
- Optional EN→AR output: glossary for categorical labels, Qwen3-4B (transformers or
  Ollama) for free text, consistent Arabic speaker labels.
- WebSocket streaming endpoint with an example client.
- Bilingual Streamlit UI with right-to-left Arabic layout, charts and text/JSON export.
- Runs on NVIDIA GPUs (Docker), Apple Silicon (MPS, native) and CPU (Docker).
- Test suite runs without model weights; CI with ruff and pytest.
