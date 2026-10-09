"""Map application exceptions to HTTP responses."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.core.exceptions import (
    AudioDecodeError,
    ModelNotReadyError,
    PayloadTooLargeError,
    SawtError,
    StreamProtocolError,
    TooManySessionsError,
)

STATUS_CODES: dict[type[SawtError], int] = {
    ModelNotReadyError: 503,
    AudioDecodeError: 422,
    PayloadTooLargeError: 413,
    TooManySessionsError: 429,
    StreamProtocolError: 400,
}


def status_code_for(exc: SawtError) -> int:
    for exc_type, code in STATUS_CODES.items():
        if isinstance(exc, exc_type):
            return code
    return 500


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(SawtError)
    async def _handle(_: Request, exc: SawtError) -> JSONResponse:
        return JSONResponse(status_code=status_code_for(exc), content={"detail": str(exc)})
