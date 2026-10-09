"""Reject oversized request bodies before Starlette spools them to disk."""

from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

# Room for the multipart boundaries and form fields around the uploaded file.
MULTIPART_OVERHEAD_BYTES = 64 * 1024


class BodySizeLimitMiddleware:
    """413 when the declared Content-Length, or the body received so far, exceeds the upload limit."""

    def __init__(self, app: ASGIApp, max_upload_bytes: int):
        self.app = app
        self.limit = max_upload_bytes + MULTIPART_OVERHEAD_BYTES
        self.detail = f"Upload exceeds {max_upload_bytes // (1024 * 1024)} MB"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        declared = dict(scope["headers"]).get(b"content-length", b"")
        if declared.isdigit() and int(declared) > self.limit:
            await JSONResponse({"detail": self.detail}, status_code=413)(scope, receive, send)
            return

        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            received += len(message.get("body", b""))
            if received > self.limit:
                # An HTTPException, because FastAPI turns any other error while parsing a body into a 400.
                raise HTTPException(413, self.detail)
            return message

        await self.app(scope, limited_receive, send)
