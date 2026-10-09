"""Per-session state: the latest result and the outcome of the last analysis run."""

from dataclasses import dataclass
from typing import Any

import streamlit as st


@dataclass(frozen=True)
class Outcome:
    """How the last analysis ended; shown once, on the rerun that follows it."""

    elapsed_s: float
    error: dict[str, Any] | None = None


_DEFAULTS: dict[str, Any] = {
    "result": None,
    "file_name": None,
    "analyzing": False,
    "outcome": None,
}


def init() -> None:
    for key, value in _DEFAULTS.items():
        st.session_state.setdefault(key, value)


def is_analyzing() -> bool:
    return st.session_state["analyzing"]


def start_analysis() -> None:
    st.session_state["analyzing"] = True


def finish_analysis(response: dict[str, Any], file_name: str, elapsed_s: float) -> None:
    """Store an API response (result or error dict) and end the analysis run."""
    failed = "error" in response
    st.session_state.update(
        analyzing=False,
        result=None if failed else response,
        file_name=None if failed else file_name,
        outcome=Outcome(elapsed_s, response if failed else None),
    )


def result() -> dict[str, Any] | None:
    return st.session_state["result"]


def file_name() -> str:
    return st.session_state["file_name"] or "audio"


def pop_outcome() -> Outcome | None:
    return st.session_state.pop("outcome", None)
