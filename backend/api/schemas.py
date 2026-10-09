"""Request/response models that appear in the OpenAPI docs (``/docs``).

Analysis results are returned as JSON objects whose shape is documented in
``docs/api.md`` and typed in ``backend/domain/entities.py``; their ``analysis``
section is produced by the language model.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field


class ModelState(BaseModel):
    name: str
    state: Literal["pending", "loading", "ready", "failed", "disabled"]
    error: str | None = None


class HealthResponse(BaseModel):
    status: Literal["loading", "ready", "degraded", "unavailable"]
    version: str
    device: str
    models: dict[str, ModelState]
    translation_available: bool
    diarization_available: bool


class ErrorResponse(BaseModel):
    detail: str


AnalysisResponse = dict[str, Any]


# ----------------------------------------------------------------- WebSocket protocol


class StreamStart(BaseModel):
    """First client message on ``/api/v1/conversations/stream``."""

    type: Literal["start"]
    translate: bool = False
    filename: str = Field(default="stream.wav", max_length=255)


class StreamEnd(BaseModel):
    type: Literal["end"]
