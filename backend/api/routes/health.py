from fastapi import APIRouter, Depends

from backend import __version__
from backend.api.dependencies import get_container
from backend.api.schemas import HealthResponse, ModelState
from backend.container import Container

router = APIRouter(tags=["health"])


@router.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"name": "sawt", "version": __version__, "docs": "/docs", "health": "/health"}


@router.get("/health", response_model=HealthResponse)
def health(container: Container = Depends(get_container)) -> HealthResponse:
    """Readiness and the state of each model."""
    registry = container.registry
    models = {key: ModelState(**vars(status)) for key, status in registry.status.items()}
    states = {key: m.state for key, m in models.items()}

    if container.loading or states["audio_llm"] in ("pending", "loading"):
        status = "loading"
    elif not container.ready:
        status = "unavailable"
    elif "failed" in states.values():
        status = "degraded"
    else:
        status = "ready"

    return HealthResponse(
        status=status,
        version=__version__,
        device=registry.device,
        models=models,
        translation_available=container.translator.available,
        diarization_available=registry.diarizer is not None,
    )
