"""
backend/services/llm/base.py

The LLMProvider interface plus a shared HTTP base for the real providers.

Design notes
------------
- Providers are called directly over their REST APIs with httpx rather than
  through vendor SDKs. The report layer makes exactly one JSON-mode call per
  report, so an SDK would add dependencies and a second exception hierarchy to
  normalize without buying anything for that one call.
- HTTPLLMProvider owns all the failure mapping, so "429 means LLMRateLimitError"
  is decided once instead of twice and can't drift between vendors. Subclasses
  only describe how to build their payload and where the text sits in the
  response.
- The httpx.AsyncClient is injected, not created here: it is built once during
  app startup and closed at shutdown, mirroring how the model is loaded exactly
  once rather than per request.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import httpx

from backend.core.logging import get_logger
from backend.utils.exceptions import LLMProviderError, LLMRateLimitError, LLMTimeoutError

logger = get_logger(__name__)


class LLMProvider(ABC):
    """One text-in, text-out call to a language model."""

    name: str = "base"

    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Run one completion and return the raw text response.

        Implementations request JSON output where the API supports it, but make
        no promise the text is valid JSON -- parsing and schema validation are
        the report service's job, including the retry.

        Raises:
            LLMTimeoutError, LLMRateLimitError, LLMProviderError.
        """


class HTTPLLMProvider(LLMProvider):
    """Shared plumbing for providers reached over HTTP."""

    def __init__(self, client: httpx.AsyncClient, model: str, api_key: str, timeout_seconds: float):
        self._client = client
        self._model = model
        self._api_key = api_key
        self._timeout = timeout_seconds

    async def _post(self, url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        """POST JSON and return the decoded body, mapping every failure mode to a typed error."""
        try:
            response = await self._client.post(url, json=payload, headers=headers, timeout=self._timeout)
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError(
                f"{self.name} did not respond within {self._timeout:.0f}s."
            ) from exc
        except httpx.RequestError as exc:
            raise LLMProviderError(f"Could not reach {self.name}: {exc}") from exc

        if response.status_code == 429:
            raise LLMRateLimitError(f"{self.name} rate limit exceeded. Try again shortly.")
        if response.status_code >= 400:
            # Truncated: provider error bodies can be long, and the full body may
            # echo the prompt back into the log.
            raise LLMProviderError(
                f"{self.name} returned HTTP {response.status_code}: {response.text[:300]}"
            )

        try:
            return response.json()
        except ValueError as exc:
            raise LLMProviderError(f"{self.name} returned a non-JSON response body.") from exc
