"""FastAPI dependencies."""

from fastapi import Request

from backend.container import Container
from backend.core.exceptions import ModelNotReadyError


def get_container(request: Request) -> Container:
    return request.app.state.container


def require_ready(request: Request) -> Container:
    container: Container = request.app.state.container
    if not container.ready:
        state = "loading" if container.loading else "unavailable"
        raise ModelNotReadyError(f"Models are {state}; check GET /health")
    return container
