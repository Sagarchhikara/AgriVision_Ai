"""
backend/services/llm/gemini.py

Google Gemini provider (generativeLanguage REST API).

Uses responseMimeType="application/json" so the model is constrained to emit a
bare JSON object, which removes the most common parse failure (a JSON body
wrapped in markdown code fences). The retry in the report service still exists
because JSON mode constrains the syntax, not the schema.
"""

from __future__ import annotations

from typing import Any

from backend.core.logging import get_logger
from backend.services.llm.base import HTTPLLMProvider
from backend.utils.exceptions import LLMProviderError

logger = get_logger(__name__)

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(HTTPLLMProvider):
    name = "gemini"

    def __init__(self, client, model: str, api_key: str, timeout_seconds: float,
                 temperature: float, max_output_tokens: int):
        super().__init__(client, model, api_key, timeout_seconds)
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        payload: dict[str, Any] = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": self._temperature,
                "maxOutputTokens": self._max_output_tokens,
                "responseMimeType": "application/json",
            },
        }
        body = await self._post(
            f"{API_BASE}/{self._model}:generateContent",
            payload=payload,
            headers={"x-goog-api-key": self._api_key, "Content-Type": "application/json"},
        )
        return _extract_text(body)


def _extract_text(body: dict[str, Any]) -> str:
    """
    Pull the generated text out of a Gemini response.

    A response with no candidates is a real, non-exceptional outcome here (for
    example a safety block), so it gets an explicit error rather than an
    IndexError from optimistic indexing.
    """
    candidates = body.get("candidates") or []
    if not candidates:
        reason = body.get("promptFeedback", {}).get("blockReason", "no candidates returned")
        raise LLMProviderError(f"Gemini returned no usable output ({reason}).")

    parts = candidates[0].get("content", {}).get("parts") or []
    text = "".join(part.get("text", "") for part in parts)
    if not text.strip():
        finish_reason = candidates[0].get("finishReason", "unknown")
        raise LLMProviderError(f"Gemini returned empty output (finishReason={finish_reason}).")
    return text
