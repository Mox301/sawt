"""FastAPI application factory.

Run with:  uvicorn backend.main:create_app --factory
Models load in a background thread so the server answers /api/v1/health immediately.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend import __version__
from backend.api.errors import register_error_handlers
from backend.api.routes import conversations, health
from backend.container import Container
from backend.core.config import Settings, get_settings
from backend.core.logging import setup_logging
from backend.infrastructure.ml.registry import ModelRegistry

logger = logging.getLogger(__name__)


def _log_crash(task: asyncio.Task) -> None:
    if not task.cancelled() and task.exception():
        logger.error("Model loading crashed: %s", task.exception())


def create_app(
    settings: Settings | None = None,
    registry: ModelRegistry | None = None,
    load_in_background: bool = True,
) -> FastAPI:
    settings = settings or get_settings()
    setup_logging(settings.log_level)
    container = Container(settings, registry or ModelRegistry(settings))

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if load_in_background:
            container.loading = True
            task = asyncio.create_task(asyncio.to_thread(container.load))
            task.add_done_callback(_log_crash)
        else:
            container.load()
        yield

    app = FastAPI(
        title="Sawt API",
        description="Bilingual (Arabic/English) multi-speaker conversation analysis with audio LLMs.",
        version=__version__,
        lifespan=lifespan,
    )
    app.state.container = container
    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(conversations.router)
    return app
