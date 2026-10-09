"""Text model adapter (``TextLLM``) backed by a local Ollama server.

Useful on Apple Silicon, where Ollama runs a quantized model on the GPU and leaves
unified memory free for the audio model.
"""

import logging
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor

import httpx

logger = logging.getLogger(__name__)

PARALLEL_REQUESTS = 4
REQUEST_TIMEOUT_S = 300


class OllamaTextLLM:
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client = httpx.Client(timeout=REQUEST_TIMEOUT_S)
        self._check_model_available()

    def _check_model_available(self) -> None:
        response = self._client.get(f"{self.base_url}/api/tags")
        response.raise_for_status()
        names = {m.get("name") for m in response.json().get("models", [])}
        if self.model not in names:
            raise RuntimeError(f"Ollama model '{self.model}' not found; run: ollama pull {self.model}")
        logger.info("Using Ollama model %s at %s", self.model, self.base_url)

    def generate_batch(self, prompts: Sequence[str], max_new_tokens: int) -> list[str]:
        with ThreadPoolExecutor(max_workers=PARALLEL_REQUESTS) as pool:
            return list(pool.map(lambda p: self._generate(p, max_new_tokens), prompts))

    def _generate(self, prompt: str, max_new_tokens: int) -> str:
        try:
            response = self._client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {"num_predict": max_new_tokens},
                },
            )
            response.raise_for_status()
            return response.json()["message"]["content"].strip()
        except (httpx.HTTPError, KeyError) as e:
            logger.error("Ollama generation failed: %s", e)
            return ""
