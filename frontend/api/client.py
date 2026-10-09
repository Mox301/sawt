"""HTTP client for the Sawt API.

Every call returns the decoded JSON body on success, or an error dict
``{"error": <title>, "message": <text>, "technical_details"?: <text>}`` instead of raising.
"""

from typing import Any

import requests

from frontend.core.settings import ANALYSIS_TIMEOUT_S, API_URL, HEALTH_TIMEOUT_S

Response = dict[str, Any]

_HTTP_ERRORS: dict[int, tuple[str, str]] = {
    413: ("File Too Large", "The file exceeds the API's upload limit."),
    422: ("Invalid Audio", "The file could not be decoded as audio."),
    503: ("Models Not Ready", "The analysis models are still loading. Try again in a minute."),
}


def get_health() -> Response:
    try:
        response = requests.get(f"{API_URL}/health", timeout=HEALTH_TIMEOUT_S)
    except requests.RequestException as exc:
        return _transport_error(exc)
    return _decode(response)


def analyze_conversation(audio: bytes, filename: str, *, translate: bool, content_type: str | None = None) -> Response:
    try:
        response = requests.post(
            f"{API_URL}/v1/conversation",
            files={"audio": (filename, audio, content_type)},
            data={"translate": "true" if translate else "false"},
            timeout=ANALYSIS_TIMEOUT_S,
        )
    except requests.RequestException as exc:
        return _transport_error(exc)
    return _decode(response)


def _decode(response: requests.Response) -> Response:
    if not response.ok:
        return _http_error(response)
    try:
        return response.json()
    except ValueError:
        return {"error": "Invalid Response", "message": "The API returned a response that is not JSON."}


def _http_error(response: requests.Response) -> Response:
    code = response.status_code
    title, message = _HTTP_ERRORS.get(code, ("HTTP Error", f"The API returned HTTP {code}."))
    try:
        detail = response.json().get("detail")
    except (ValueError, AttributeError):
        detail = None
    if detail:
        return {"error": title, "message": str(detail)}
    return {"error": title, "message": message, "technical_details": response.text[:500]}


def _transport_error(exc: requests.RequestException) -> Response:
    if isinstance(exc, requests.Timeout):
        title, message = "Timeout", "The API did not respond in time."
    elif isinstance(exc, requests.ConnectionError):
        title, message = "Connection Error", f"Could not connect to the Sawt API at {API_URL}."
    else:
        title, message = "Request Failed", "The request to the API failed."
    return {"error": title, "message": message, "technical_details": str(exc)}
