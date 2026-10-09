"""Per-session state: the latest result, the running analysis and the outcome of the last one."""

import time
from concurrent.futures import Future
from dataclasses import dataclass
from typing import Any

import streamlit as st


@dataclass(frozen=True)
class Outcome:
    """How the last analysis ended; shown once, on the rerun that follows it."""

    elapsed_s: float
    error: dict[str, Any] | None = None


@dataclass(frozen=True)
class Job:
    """An analysis request running in a worker thread, kept here so it survives reruns."""

    future: Future[dict[str, Any]]
    file_name: str
    started_s: float

    @property
    def elapsed_s(self) -> float:
        return time.perf_counter() - self.started_s


_DEFAULTS: dict[str, Any] = {
    "result": None,
    "file_name": None,
    "job": None,
    "outcome": None,
}


def init() -> None:
    for key, value in _DEFAULTS.items():
        st.session_state.setdefault(key, value)


def current_job() -> Job | None:
    return st.session_state["job"]


def is_analyzing() -> bool:
    return current_job() is not None


def start_analysis(future: Future[dict[str, Any]], file_name: str) -> None:
    st.session_state["job"] = Job(future, file_name, time.perf_counter())


def finish_analysis(job: Job) -> None:
    """Store a finished job's API response (result or error dict) and clear the job."""
    try:
        response = job.future.result()
    except Exception as exc:  # The client returns error dicts; this keeps a bug from wedging the session.
        response = {"error": "Request Failed", "message": str(exc)}
    failed = "error" in response
    st.session_state["result"] = None if failed else response
    st.session_state["file_name"] = None if failed else job.file_name
    st.session_state["outcome"] = Outcome(job.elapsed_s, response if failed else None)
    # Last: each write can raise a rerun request. One that lands earlier leaves the job for the next run to finish.
    st.session_state["job"] = None


def result() -> dict[str, Any] | None:
    return st.session_state["result"]


def file_name() -> str:
    return st.session_state["file_name"] or "audio"


def pop_outcome() -> Outcome | None:
    return st.session_state.pop("outcome", None)
