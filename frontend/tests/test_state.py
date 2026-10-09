from collections import UserDict
from concurrent.futures import Future
from typing import Any

import pytest

from frontend.core import state


class _RecordingState(UserDict):
    """A session state that records the order of its writes (``update`` included, as in Streamlit)."""

    def __init__(self) -> None:
        self.writes: list[str] = []
        super().__init__()

    def __setitem__(self, key: str, value: Any) -> None:
        self.writes.append(key)
        super().__setitem__(key, value)


@pytest.fixture
def session(monkeypatch) -> _RecordingState:
    recording = _RecordingState()
    monkeypatch.setattr(state.st, "session_state", recording)
    state.init()
    return recording


def _finished_job(response: dict[str, Any]) -> state.Job:
    future: Future[dict[str, Any]] = Future()
    future.set_result(response)
    return state.Job(future, "call.wav", started_s=0.0)


def test_finish_clears_the_job_last(session):
    job = _finished_job({"analysis": {}})
    state.start_analysis(job.future, job.file_name)
    session.writes.clear()

    state.finish_analysis(job)

    # A rerun request raised by any earlier write leaves the job, and the next run finishes it again.
    assert session.writes[-1] == "job"
    assert session["job"] is None
    assert session["result"] == {"analysis": {}}
    assert session["file_name"] == "call.wav"
    assert session["outcome"].error is None


def test_finishing_again_is_idempotent(session):
    job = _finished_job({"error": "Timeout", "message": "The API did not respond in time."})

    state.finish_analysis(job)
    first = (session["result"], session["file_name"], session["outcome"].error)
    state.finish_analysis(job)

    assert (session["result"], session["file_name"], session["outcome"].error) == first
    assert first == (None, None, {"error": "Timeout", "message": "The API did not respond in time."})
