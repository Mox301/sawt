from fastapi import APIRouter, Depends, File, Form, UploadFile

from backend.api.dependencies import require_ready
from backend.api.schemas import AnalysisResponse, ErrorResponse
from backend.container import Container
from backend.core.exceptions import PayloadTooLargeError
from backend.infrastructure.audio_io import prepared_audio

router = APIRouter(prefix="/v1", tags=["analysis"])

ERRORS = {
    413: {"model": ErrorResponse, "description": "Upload exceeds SAWT_MAX_UPLOAD_MB"},
    422: {"model": ErrorResponse, "description": "File could not be decoded as audio"},
    503: {"model": ErrorResponse, "description": "Models are still loading"},
}


async def _read_upload(audio: UploadFile, max_bytes: int) -> bytes:
    data = await audio.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise PayloadTooLargeError(f"Upload exceeds {max_bytes // (1024 * 1024)} MB")
    return data


@router.post("/conversation", response_model=AnalysisResponse, responses=ERRORS)
async def analyze_conversation(
    audio: UploadFile = File(..., description="Audio file (wav, mp3, m4a, flac, ogg …)"),
    translate: bool = Form(False, description="Also return an Arabic version: {EN, AR}"),
    container: Container = Depends(require_ready),
) -> AnalysisResponse:
    """Multi-speaker conversation analysis: diarization, prosody, turn-taking and the
    audio-LLM's conversation, speaker and interaction analysis."""
    data = await _read_upload(audio, container.settings.max_upload_bytes)
    filename = audio.filename or "upload"

    def run():
        with prepared_audio(data) as prepared:
            return container.conversation.analyze(prepared, filename, translate)

    return await container.gate.run(run)


@router.post("/sentiment", response_model=AnalysisResponse, responses=ERRORS)
async def analyze_sentiment(
    audio: UploadFile = File(..., description="Audio file (wav, mp3, m4a, flac, ogg …)"),
    translate: bool = Form(False, description="Also return an Arabic version: {EN, AR}"),
    container: Container = Depends(require_ready),
) -> AnalysisResponse:
    """Overall sentiment (Positive / Negative / Neutral) with a short justification."""
    data = await _read_upload(audio, container.settings.max_upload_bytes)

    def run():
        with prepared_audio(data) as prepared:
            return container.sentiment.analyze(prepared, translate)

    return await container.gate.run(run)
