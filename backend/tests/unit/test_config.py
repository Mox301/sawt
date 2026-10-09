import sys
from types import SimpleNamespace

import pytest

from backend.core.config import Settings
from backend.infrastructure.ml import download
from backend.infrastructure.ml.registry import ModelRegistry


@pytest.mark.parametrize(("line", "expected"), [("HF_TOKEN=hf_abc", "hf_abc"), ("HF_TOKEN=", None)])
def test_hf_token_is_read_from_the_env_file(tmp_path, monkeypatch, line, expected):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(f"{line}\n")
    settings = Settings(_env_file=env_file)
    assert settings.hf_token == expected
    assert "hf_abc" not in repr(settings)


def test_hf_token_is_not_prefixed(monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.setenv("SAWT_HF_TOKEN", "ignored")
    assert Settings(_env_file=None).hf_token is None
    monkeypatch.setenv("HF_TOKEN", "from-env")
    assert Settings(_env_file=None).hf_token == "from-env"


def test_hf_token_reaches_the_downloader_and_the_diarizer(monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "hf_abc")
    settings = Settings(_env_file=None, translation_backend="off")

    tokens = []
    monkeypatch.setattr(download, "get_settings", lambda: settings)
    monkeypatch.setattr(download, "snapshot_download", lambda repo, **kwargs: tokens.append(kwargs["token"]))
    download.main()
    assert tokens == ["hf_abc", "hf_abc"]

    class FakeDiarizer:
        def __init__(self, model_id, device, token):
            tokens.append(token)

    device = SimpleNamespace(
        resolve_device=lambda _: "cpu", resolve_dtype=lambda *_: "fp32", attention_implementation=lambda _: None
    )
    ml = "backend.infrastructure.ml"
    monkeypatch.setitem(sys.modules, f"{ml}.device", device)
    monkeypatch.setitem(sys.modules, f"{ml}.pyannote", SimpleNamespace(PyannoteDiarizer=FakeDiarizer))
    monkeypatch.setitem(sys.modules, f"{ml}.voxtral", None)  # never load real weights
    registry = ModelRegistry(settings)
    registry.load_all()
    assert tokens[-1] == "hf_abc" and registry.status["diarization"].state == "ready"
