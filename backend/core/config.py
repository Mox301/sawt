"""Application settings, read from ``SAWT_*`` environment variables (and ``.env``)."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

Device = Literal["auto", "cuda", "mps", "cpu"]
DType = Literal["auto", "bf16", "fp16", "fp32"]
TranslationBackend = Literal["transformers", "ollama", "off"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SAWT_", env_file=".env", extra="ignore")

    # Inference hardware
    device: Device = "auto"
    dtype: DType = "auto"

    # Models (Hugging Face ids, resolved from the local HF cache)
    audio_model: str = "mistralai/Voxtral-Mini-3B-2507"
    diarization_model: str = "pyannote/speaker-diarization-community-1"
    enable_diarization: bool = True

    # EN→AR translation of the analysis
    translation_backend: TranslationBackend = "transformers"
    translation_model: str = "Qwen/Qwen3-4B-Instruct-2507"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:4b-instruct-2507-q4_K_M"

    # Limits
    max_upload_mb: int = 100
    stream_max_sessions: int = 10
    stream_idle_timeout_s: int = 300

    log_level: str = "INFO"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
