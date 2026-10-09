"""Pick the torch device and dtype for the current machine."""

import torch

from backend.core.config import Device, DType

_DTYPES = {"bf16": torch.bfloat16, "fp16": torch.float16, "fp32": torch.float32}


def resolve_device(preference: Device = "auto") -> str:
    if preference != "auto":
        return preference
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def resolve_dtype(device: str, preference: DType = "auto") -> torch.dtype:
    """bf16 on CUDA and CPU; fp16 on Apple MPS, where bf16 support is incomplete."""
    if preference != "auto":
        return _DTYPES[preference]
    return torch.float16 if device == "mps" else torch.bfloat16


def attention_implementation(device: str) -> str | None:
    """Eager attention on MPS (SDPA kernels there are less reliable); library default elsewhere."""
    return "eager" if device == "mps" else None
