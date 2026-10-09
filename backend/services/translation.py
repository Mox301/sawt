"""EN→AR translation of analysis results.

Walks the result, collects every translatable string and resolves each one, in
order of preference:
  1. already Arabic, too short or numeric → kept as is,
  2. a fixed glossary term or a bare speaker id → translated deterministically,
  3. anything else → batched to the text model, with speaker references masked so
     they come back as consistent Arabic labels.

Returns ``{"EN": <original>, "AR": <translated>}``. Without a usable text model it
returns the English result with ``metadata.translation`` set instead.
"""

import copy
import logging
from typing import Any

from backend.domain.arabic import (
    NON_TRANSLATABLE_KEYS,
    glossary_lookup,
    is_arabic,
    is_speaker_id,
    mask_speaker_refs,
    replace_speaker_refs,
    unmask_speaker_refs,
)
from backend.infrastructure.ml.interfaces import TextLLM
from backend.prompts.translation import build_translation_prompt

logger = logging.getLogger(__name__)

MAX_NEW_TOKENS = 2048

Path = list[str | int]


class TranslationService:
    def __init__(self, text_llm: TextLLM | None):
        self.text_llm = text_llm

    @property
    def available(self) -> bool:
        return self.text_llm is not None

    def translate(self, result: dict[str, Any]) -> dict[str, Any]:
        if not self.available:
            return _mark_untranslated(result, "unavailable")
        try:
            return {"EN": result, "AR": self._translate(copy.deepcopy(result))}
        except Exception:
            logger.exception("Translation failed")
            return _mark_untranslated(result, "failed")

    def _translate(self, data: dict[str, Any]) -> dict[str, Any]:
        paths: list[Path] = []
        texts: list[str] = []
        _collect(data, [], paths, texts)

        pending: list[tuple[int, str, dict[str, str]]] = []  # (index, masked text, placeholders)
        for i, text in enumerate(texts):
            resolved = _resolve_locally(text)
            if resolved is not None:
                _set(data, paths[i], resolved)
            else:
                masked, placeholders = mask_speaker_refs(text.strip())
                pending.append((i, masked, placeholders))

        if pending:
            logger.info("Translating %d of %d text fields with the text model", len(pending), len(texts))
            prompts = [build_translation_prompt(masked) for _, masked, _ in pending]
            outputs = self.text_llm.generate_batch(prompts, MAX_NEW_TOKENS)
            for (i, _, placeholders), output in zip(pending, outputs, strict=True):
                _set(data, paths[i], _clean_output(output, placeholders) or texts[i])
        return data


def _resolve_locally(text: str) -> str | None:
    """Translation that needs no model, or ``None`` when the text model is required."""
    if not text or is_arabic(text):
        return text
    stripped = text.strip()
    if len(stripped) < 2 or stripped.replace(".", "").replace("%", "").replace(",", "").isdigit():
        return text
    if (term := glossary_lookup(stripped)) is not None:
        return term
    if is_speaker_id(stripped):
        return replace_speaker_refs(stripped)
    return None


def _clean_output(output: str, placeholders: dict[str, str]) -> str:
    translation = output.strip()
    if "\n\n" in translation:  # keep the translation, drop any trailing commentary
        translation = translation.split("\n\n")[0].strip()
    return unmask_speaker_refs(translation, placeholders)


def _collect(data: Any, path: Path, paths: list[Path], texts: list[str]) -> None:
    if isinstance(data, dict):
        for key, value in data.items():
            if key not in NON_TRANSLATABLE_KEYS:
                _collect(value, path + [key], paths, texts)
    elif isinstance(data, list):
        for i, value in enumerate(data):
            _collect(value, path + [i], paths, texts)
    elif isinstance(data, str):
        paths.append(path)
        texts.append(data)


def _set(root: Any, path: Path, value: Any) -> None:
    for key in path[:-1]:
        root = root[key]
    root[path[-1]] = value


def _mark_untranslated(result: dict[str, Any], reason: str) -> dict[str, Any]:
    marked = dict(result)
    marked["metadata"] = {**result.get("metadata", {}), "translation": reason}
    return marked
