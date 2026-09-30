"""
backend/services/llm/openai.py

OpenAI provider (chat completions REST API).

Uses response_format={"type": "json_object"} for the same reason the Gemini
provider sets a JSON mime type: it removes markdown-fence wrapping as a failure
mode, without guaranteeing the object matches ReportSchema.
"""

from __future__ import annotations

from typing import Any

from backend.core.logging import get_logger
from backend.services.llm.base import HTTPLLMProvider
from backend.utils.exceptions import LLMProviderError

logger = get_logger(__name__)

API_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIProvider(HTTPLLMProvider):
    name = "openai"

    def __init__(self, client, model: str, api_key: str, timeout_seconds: float,
                 temperature: float, max_output_tokens: int):
        super().__init__(client, model, api_key, timeout_seconds)
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self._temperature,
            "max_completion_tokens": self._max_output_tokens,
            "response_format": {"type": "json_object"},
        }
        body = await self._post(
            API_URL,
            payload=payload,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
        )
        return _extract_text(body)


def _extract_text(body: dict[str, Any]) -> str:
    choices = body.get("choices") or []
    if not choices:
        raise LLMProviderError("OpenAI returned no choices.")

    content = (choices[0].get("message") or {}).get("content") or ""
    if not content.strip():
        finish_reason = choices[0].get("finish_reason", "unknown")
        raise LLMProviderError(f"OpenAI returned empty output (finish_reason={finish_reason}).")
    return content
