"""Application exceptions. The API layer maps these to HTTP/WebSocket errors."""


class SawtError(Exception):
    """Base class for all application errors."""


class ModelNotReadyError(SawtError):
    """The audio model is still loading or failed to load."""


class AudioDecodeError(SawtError):
    """The uploaded bytes could not be decoded as audio."""


class PayloadTooLargeError(SawtError):
    """The upload or stream exceeds the configured size limit."""


class TooManySessionsError(SawtError):
    """All streaming slots are in use."""


class StreamProtocolError(SawtError):
    """A WebSocket client sent an unexpected message or went idle."""
