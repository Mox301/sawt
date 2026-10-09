"""Serialises model inference and keeps it off the event loop.

One accelerator runs one request at a time; concurrent requests wait their turn
while the server keeps answering health checks and WebSocket messages.
"""

import asyncio
from collections.abc import Callable
from typing import TypeVar

from starlette.concurrency import run_in_threadpool

T = TypeVar("T")


class InferenceGate:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()

    async def run(self, fn: Callable[..., T], *args, **kwargs) -> T:
        async with self._lock:
            return await run_in_threadpool(fn, *args, **kwargs)
