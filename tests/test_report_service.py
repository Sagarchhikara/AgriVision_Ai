"""
tests/test_report_service.py

Covers the behavior that makes this layer safe rather than just functional:
variant selection, the low-confidence guarantees, the single parse retry, and
the cache.
"""

from __future__ import annotations

import pytest

from backend.schemas.report import ReportSchema, Severity
from backend.services.llm.fake import FakeProvider
from backend.utils.exceptions import (
    LLMProviderError,
    ReportDisabledError,
    ReportParseError,
)
from tests.conftest import make_request, report_json


async def test_valid_output_produces_report(service, provider):
    result = await service.generate(make_request())

    assert isinstance(result.report, ReportSchema)
    assert result.report.severity is Severity.HIGH
    assert result.cached is False
    assert result.provider == "fake"
    assert result.prompt_version
    assert provider.call_count == 1


async def test_schema_validation_rejects_bad_severity(make_service):
    provider = FakeProvider([report_json(severity="catastrophic")] * 2)
    service = make_service(provider)

    with pytest.raises(ReportParseError):
        await service.generate(make_request())


async def test_schema_validation_rejects_missing_field(make_service):
    incomplete = report_json()
    incomplete = incomplete.replace('"summary"', '"not_summary"')
    service = make_service(FakeProvider([incomplete] * 2))

    with pytest.raises(ReportParseError):
        await service.generate(make_request())


async def test_low_confidence_hedges(service, provider):
    result = await service.generate(make_request(confidence=0.31))

    assert result.report.is_low_confidence is True
    # Alternatives come from the real top-k, not from whatever the LLM echoed.
    assert result.report.possible_alternatives == ["Tomato - Early blight", "Tomato - healthy"]

    _, user_prompt = provider.prompts[0]
    assert "NOT give a definitive diagnosis" in user_prompt
    assert "plain background" in user_prompt


async def test_high_confidence_is_not_flagged(service, provider):
    result = await service.generate(make_request(confidence=0.97))

    assert result.report.is_low_confidence is False
    assert result.report.possible_alternatives == []
    assert "NOT give a definitive diagnosis" not in provider.prompts[0][1]


async def test_healthy_class_uses_healthy_variant(service, provider):
    await service.generate(make_request(predicted_class="Tomato___healthy", confidence=0.95))

    user_prompt = provider.prompts[0][1]
    assert "found no disease" in user_prompt
    assert "there is nothing to treat" in user_prompt


async def test_low_confidence_beats_healthy(service, provider):
    """A weak 'healthy' prediction must not reassure the farmer."""
    result = await service.generate(
        make_request(predicted_class="Tomato___healthy", confidence=0.30)
    )

    assert result.report.is_low_confidence is True
    assert "NOT give a definitive diagnosis" in provider.prompts[0][1]


async def test_malformed_json_retries_once_and_succeeds(make_service):
    provider = FakeProvider(["this is not json at all", report_json()])
    service = make_service(provider)

    result = await service.generate(make_request())

    assert result.report.disease_name == "Late blight"
    assert provider.call_count == 2
    # The retry must tell the model what went wrong, not just repeat itself.
    assert "could not be parsed" in provider.prompts[1][1]


async def test_malformed_json_raises_after_one_retry(make_service):
    provider = FakeProvider(["still not json", "nope, not json either"])
    service = make_service(provider)

    with pytest.raises(ReportParseError):
        await service.generate(make_request())

    assert provider.call_count == 2


async def test_markdown_fenced_json_is_accepted(make_service):
    provider = FakeProvider([f"```json\n{report_json()}\n```"])
    service = make_service(provider)

    result = await service.generate(make_request())

    assert result.report.crop == "Tomato"
    assert provider.call_count == 1


async def test_provider_error_is_not_retried(make_service):
    provider = FakeProvider([LLMProviderError("upstream exploded")])
    service = make_service(provider)

    with pytest.raises(LLMProviderError):
        await service.generate(make_request())

    assert provider.call_count == 1


async def test_cache_hit_avoids_second_call(service, provider):
    first = await service.generate(make_request(confidence=0.97))
    second = await service.generate(make_request(confidence=0.97))

    assert first.cached is False
    assert second.cached is True
    assert provider.call_count == 1


async def test_cache_misses_on_different_language(service, provider):
    await service.generate(make_request(language="en"))
    await service.generate(make_request(language="hi"))

    assert provider.call_count == 2


async def test_cache_hit_within_confidence_bucket(service, provider):
    await service.generate(make_request(confidence=0.912))
    result = await service.generate(make_request(confidence=0.954))

    assert result.cached is True
    assert provider.call_count == 1


async def test_disabled_layer_raises(make_service, provider):
    service = make_service(provider, llm_enabled=False)

    with pytest.raises(ReportDisabledError):
        await service.generate(make_request())

    assert provider.call_count == 0
