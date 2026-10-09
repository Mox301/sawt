"""Text model adapter (``TextLLM``) using Hugging Face transformers, e.g. Qwen3-4B-Instruct."""

import logging
from collections.abc import Sequence

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger(__name__)

BATCH_SIZE = 8
MAX_INPUT_TOKENS = 4096


class TransformersTextLLM:
    def __init__(self, model_id: str, device: str):
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.tokenizer.padding_side = "left"
        if device == "cuda":
            self.model = AutoModelForCausalLM.from_pretrained(model_id, dtype="auto", device_map="auto")
        else:
            self.model = AutoModelForCausalLM.from_pretrained(model_id, dtype="auto").to(device)
        self.model.eval()
        logger.info("Translation model %s loaded on %s", model_id, device)

    def generate_batch(self, prompts: Sequence[str], max_new_tokens: int) -> list[str]:
        results: list[str] = []
        for start in range(0, len(prompts), BATCH_SIZE):
            batch = list(prompts[start : start + BATCH_SIZE])
            try:
                results.extend(self._generate(batch, max_new_tokens))
            except RuntimeError as e:
                # Out-of-memory on a large batch: retry one prompt at a time.
                logger.warning("Batch generation failed (%s); retrying individually", e)
                _empty_cache()
                for prompt in batch:
                    try:
                        results.extend(self._generate([prompt], max_new_tokens))
                    except RuntimeError as single_error:
                        logger.error("Generation failed: %s", single_error)
                        results.append("")
        return results

    def _generate(self, prompts: list[str], max_new_tokens: int) -> list[str]:
        texts = [
            self.tokenizer.apply_chat_template(
                [{"role": "user", "content": p}], tokenize=False, add_generation_prompt=True
            )
            for p in prompts
        ]
        inputs = self.tokenizer(
            texts, return_tensors="pt", padding=True, truncation=True, max_length=MAX_INPUT_TOKENS
        ).to(self.model.device)
        with torch.inference_mode():
            generated = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
        prompt_len = inputs["input_ids"].shape[1]
        return [self.tokenizer.decode(ids[prompt_len:], skip_special_tokens=True).strip() for ids in generated]


def _empty_cache() -> None:
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    elif torch.backends.mps.is_available():
        torch.mps.empty_cache()
