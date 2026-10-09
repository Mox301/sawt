"""Download model weights into the Hugging Face cache.

Usage: ``python -m backend.infrastructure.ml.download`` (``make models``).
The diarization model is gated: accept its terms on huggingface.co and log in
(``hf auth login``) or set ``HF_TOKEN`` (environment or ``.env``) first.
"""

from huggingface_hub import snapshot_download

from backend.core.config import get_settings


def main() -> None:
    s = get_settings()
    repos = [s.audio_model]
    if s.enable_diarization:
        repos.append(s.diarization_model)
    if s.translation_backend == "transformers":
        repos.append(s.translation_model)

    for repo in repos:
        print(f"Downloading {repo} …", flush=True)
        # Voxtral also ships Mistral-native weights (consolidated.safetensors, ~9 GB) that transformers doesn't use.
        snapshot_download(repo, ignore_patterns=["consolidated.*"], token=s.hf_token)

    if s.translation_backend == "ollama":
        print(f"Translation runs on Ollama; pull the model with:  ollama pull {s.ollama_model}")
    print("Done.")


if __name__ == "__main__":
    main()
