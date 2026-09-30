"""
backend/services/report_service.py

Turns a model prediction into a validated, farmer-facing report.

Design notes
------------
- Confidence-awareness is the point of this service, not a feature of it. The
  classifier scores ~96% on lab photos but ~22% on real field photos, so below
  the configured threshold the service switches to a prompt that refuses to
  give a definitive diagnosis. Anything that reads as certainty on a prediction
  this weak is harmful advice, not a UX nicety.
- `is_low_confidence` and `possible_alternatives` are stamped here after
  validation rather than requested from the LLM, so the model cannot mark its
  own hedged report as confident, and the listed alternatives are always the
  real top-k rather than whatever the model remembered from the prompt.
- Exactly one retry on unparseable output, and only on parse/validation failure.
  A provider error (timeout, rate limit, HTTP 500) is not made better by asking
  again immediately, so those propagate untouched.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass

from pydantic import ValidationError

from backend.core.config import Settings
from backend.core.logging import get_logger
from backend.schemas.report import ReportRequest, ReportSchema
from backend.services.llm.base import LLMProvider
from backend.services.report_cache import ReportCache, build_cache_key
from backend.services.report_prompts import (
    PROMPT_VERSION,
    SYSTEM_PROMPT,
    PromptVariant,
    build_retry_suffix,
    build_user_prompt,
    parse_class_name,
)
from backend.utils.exceptions import ReportDisabledError, ReportParseError

logger = get_logger(__name__)


@dataclass
class GeneratedReport:
    """A report plus the provenance the API surfaces alongside it."""

    report: ReportSchema
    cached: bool
    provider: str
    prompt_version: str
    generation_time_ms: float


def _strip_code_fences(text: str) -> str:
    """
    Remove a markdown code fence wrapper if the model added one.

    JSON mode makes this rare but not impossible, and it is the single most
    common way an otherwise-perfect response fails to parse.
    """
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped

    without_open = stripped.split("\n", 1)[1] if "\n" in stripped else ""
    if without_open.rstrip().endswith("```"):
        without_open = without_open.rstrip()[: -len("```")]
    return without_open.strip()


class ReportService:
    """Generates and caches farmer-facing reports for model predictions."""

    def __init__(self, settings: Settings, provider: LLMProvider, cache: ReportCache):
        self.settings = settings
        self.provider = provider
        self.cache = cache

    def _select_variant(self, predicted_class: str, confidence: float) -> PromptVariant:
        """
        Choose which kind of report to request.

        Low confidence is checked before the healthy case on purpose: a weak
        "this plant is healthy" prediction is exactly the false negative that
        costs a farmer their crop, so it must not produce a reassuring report.
        """
        if confidence < self.settings.llm_confidence_threshold:
            return PromptVariant.LOW_CONFIDENCE
        if parse_class_name(predicted_class).is_healthy:
            return PromptVariant.HEALTHY
        return PromptVariant.STANDARD

    async def generate(self, request: ReportRequest) -> GeneratedReport:
        """
        Produce a report for one prediction, serving from cache where possible.

        Raises:
            ReportDisabledError: the LLM layer is switched off in config.
            ReportParseError: the model's output failed validation twice.
            LLMProviderError / LLMTimeoutError / LLMRateLimitError: upstream failures.
        """
        if not self.settings.llm_enabled:
            raise ReportDisabledError("Report generation is disabled on this deployment.")

        start = time.perf_counter()
        language = request.language or self.settings.llm_default_language
        top_k_names = [item.class_name for item in request.top_k]
        variant = self._select_variant(request.predicted_class, request.confidence)

        cache_key = build_cache_key(
            predicted_class=request.predicted_class,
            confidence=request.confidence,
            language=language,
            top_k_class_names=top_k_names,
            bucket_size=self.settings.llm_confidence_bucket_size,
        )

        cached_report = await self.cache.get(cache_key)
        if cached_report is not None:
            logger.info("Report cache hit for %s (variant=%s)", cache_key, variant.value)
            return GeneratedReport(
                report=cached_report,
                cached=True,
                provider=self.provider.name,
                prompt_version=PROMPT_VERSION,
                generation_time_ms=(time.perf_counter() - start) * 1000,
            )

        user_prompt = build_user_prompt(
            variant=variant,
            predicted_class=request.predicted_class,
            confidence=request.confidence,
            top_k=[(item.class_name, item.confidence) for item in request.top_k],
            language=language,
        )

        logger.info(
            "Generating report: class=%s confidence=%.4f variant=%s language=%s provider=%s",
            request.predicted_class, request.confidence, variant.value, language, self.provider.name,
        )
        report = await self._generate_validated(user_prompt)

        report.is_low_confidence = variant is PromptVariant.LOW_CONFIDENCE
        if report.is_low_confidence:
            report.possible_alternatives = _readable_alternatives(top_k_names)

        await self.cache.set(cache_key, report)

        generation_time_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "Report generated in %.1fms (variant=%s, low_confidence=%s)",
            generation_time_ms, variant.value, report.is_low_confidence,
        )
        return GeneratedReport(
            report=report,
            cached=False,
            provider=self.provider.name,
            prompt_version=PROMPT_VERSION,
            generation_time_ms=generation_time_ms,
        )

    async def _generate_validated(self, user_prompt: str) -> ReportSchema:
        """Call the provider and validate its output, retrying once on bad output."""
        raw = await self.provider.generate(SYSTEM_PROMPT, user_prompt)
        try:
            return _parse_report(raw)
        except (ValueError, ValidationError) as exc:
            # Bound to a plain string: Python unbinds `exc` at the end of the
            # except block, and the retry prompt below needs the message.
            first_error = str(exc)
            logger.warning("Report output failed validation, retrying once: %s", first_error)

        retry_prompt = user_prompt + build_retry_suffix(first_error)
        raw = await self.provider.generate(SYSTEM_PROMPT, retry_prompt)
        try:
            return _parse_report(raw)
        except (ValueError, ValidationError) as second_error:
            raise ReportParseError(
                f"The language model did not return a valid report after one retry: {second_error}"
            ) from second_error


def _parse_report(raw: str) -> ReportSchema:
    """Decode and schema-validate one raw model response."""
    data = json.loads(_strip_code_fences(raw))
    return ReportSchema.model_validate(data)


def _readable_alternatives(top_k_class_names: list[str]) -> list[str]:
    """Human-readable labels for the runner-up candidates, for a hedged report."""
    alternatives = []
    for class_name in top_k_class_names[1:]:
        parsed = parse_class_name(class_name)
        alternatives.append(f"{parsed.crop} - {parsed.disease}" if parsed.crop else parsed.disease)
    return alternatives
