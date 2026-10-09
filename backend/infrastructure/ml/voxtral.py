"""Voxtral adapter (``AudioLLM``) using Hugging Face transformers."""

import logging

import torch
from transformers import AutoProcessor, VoxtralForConditionalGeneration

logger = logging.getLogger(__name__)


class VoxtralAudioLLM:
    def __init__(self, model_id: str, device: str, dtype: torch.dtype, attn_implementation: str | None):
        self.device = device
        self.processor = AutoProcessor.from_pretrained(model_id)
        kwargs = {"dtype": dtype}
        if attn_implementation:
            kwargs["attn_implementation"] = attn_implementation
        if device == "cuda":
            self.model = VoxtralForConditionalGeneration.from_pretrained(model_id, device_map="auto", **kwargs)
        else:
            self.model = VoxtralForConditionalGeneration.from_pretrained(model_id, **kwargs).to(device)
        self.model.eval()
        logger.info("Voxtral loaded on %s (%s)", device, dtype)

    def generate(self, audio_path: str, prompt: str, max_new_tokens: int) -> str:
        conversation = [
            {
                "role": "user",
                "content": [
                    {"type": "audio", "path": audio_path},
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        inputs = self.processor.apply_chat_template(conversation, return_tensors="pt").to(self.device)
        with torch.inference_mode():
            # Greedy decoding (the model's generation config does not enable sampling).
            outputs = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
        new_tokens = outputs[:, inputs["input_ids"].shape[1] :]
        return self.processor.batch_decode(new_tokens, skip_special_tokens=True)[0]
