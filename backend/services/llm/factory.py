"""
backend/services/llm/factory.py

Builds the configured LLMProvider and resolves its API key.

Design notes
------------
- API keys are read from the environment only, never from configs/config.yaml,
  which is a tracked file. Each provider accepts its conventional variable
  (GEMINI_API_KEY / OPENAI_API_KEY) so an existing shell setup works unchanged,
  with AGRIVISION_LLM_API_KEY as a provider-agnostic override for deployments
  that inject one generic secret.
- A missing key raises at startup rather than on first request. The default
  provider is 'fake', so choosing a real one is deliberate; a deployment that
  asked for Gemini and has no key is misconfigured and should fail loudly
  before it starts serving, not on a farmer's first upload.
"""

from __future__ import annotations

import os

import httpx

from backend.core.config import Settings
from backend.core.logging import get_logger
from backend.services.llm.base import LLMProvider
from backend.services.llm.fake import FakeProvider
from backend.services.llm.gemini import GeminiProvider
from backend.services.llm.openai import OpenAIProvider
from backend.utils.exceptions import LLMConfigurationError

logger = get_logger(__name__)

GENERIC_KEY_ENV = "AGRIVISION_LLM_API_KEY"
PROVIDER_KEY_ENV = {
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
}


def resolve_api_key(provider: str) -> str:
    """Return the API key for `provider`, or raise LLMConfigurationError."""
    provider_env = PROVIDER_KEY_ENV[provider]
    key = os.environ.get(GENERIC_KEY_ENV) or os.environ.get(provider_env)
    if not key:
        raise LLMConfigurationError(
            f"LLM provider '{provider}' is selected but no API key is set. "
            f"Export {provider_env} (or {GENERIC_KEY_ENV}) and restart."
        )
    return key


def build_provider(settings: Settings, client: httpx.AsyncClient) -> LLMProvider:
    """
    Construct the provider named by `settings.llm_provider`.

    Args:
        settings: resolved backend settings.
        client: the shared AsyncClient built once at app startup. Unused by the
            fake provider, which never makes a request.
    """
    provider = settings.llm_provider

    if provider == "fake":
        logger.warning(
            "Using the fake LLM provider -- reports will be placeholder text, not real advice."
        )
        return FakeProvider()

    api_key = resolve_api_key(provider)
    provider_class = {"gemini": GeminiProvider, "openai": OpenAIProvider}[provider]

    logger.info("LLM provider '%s' ready (model=%s)", provider, settings.llm_model)
    return provider_class(
        client=client,
        model=settings.llm_model,
        api_key=api_key,
        timeout_seconds=settings.llm_timeout_seconds,
        temperature=settings.llm_temperature,
        max_output_tokens=settings.llm_max_output_tokens,
    )
