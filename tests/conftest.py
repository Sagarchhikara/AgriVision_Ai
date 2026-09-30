"""
tests/conftest.py

Shared fixtures for the report layer.

Everything here runs against FakeProvider: no network, no API keys, no cost.
The TestClient is deliberately built WITHOUT a `with` block -- Starlette only
runs the app's lifespan inside the context manager, and this app's lifespan
loads the EfficientNet checkpoint. Skipping it keeps these tests fast and lets
them pass on a machine that has no trained model at all.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from backend.api.deps import get_report_service
from backend.core.config import Settings
from backend.schemas.prediction import ClassPrediction
from backend.schemas.report import ReportRequest
from backend.services.llm.fake import FakeProvider
from backend.services.report_cache import InMemoryTTLCache
from backend.services.report_service import ReportService

VALID_REPORT: dict = {
    "disease_name": "Late blight",
    "crop": "Tomato",
    "summary": "A fast-spreading disease that rots leaves and fruit in cool, wet weather.",
    "severity": "high",
    "severity_reason": "It can destroy a tomato crop within two weeks.",
    "symptoms_to_check": ["Dark brown patches on leaves"],
    "treatment": {"organic": ["Remove affected leaves"], "chemical": []},
    "prevention": ["Avoid overhead watering late in the day"],
    "when_to_consult_expert": "Contact your local agricultural extension officer before spraying.",
    "confidence_note": "Confirm the symptoms above before treating.",
}


def report_json(**overrides) -> str:
    """Serialize a schema-valid report, with optional field overrides."""
    return json.dumps({**VALID_REPORT, **overrides})


def make_request(
    predicted_class: str = "Tomato___Late_blight",
    confidence: float = 0.97,
    language: str | None = None,
) -> ReportRequest:
    """A ReportRequest with a plausible top-3, for the common test case."""
    runner_up = 1.0 - confidence
    return ReportRequest(
        predicted_class=predicted_class,
        confidence=confidence,
        top_k=[
            ClassPrediction(class_name=predicted_class, confidence=confidence),
            ClassPrediction(class_name="Tomato___Early_blight", confidence=runner_up * 0.7),
            ClassPrediction(class_name="Tomato___healthy", confidence=runner_up * 0.3),
        ],
        language=language,
    )


@pytest.fixture
def settings() -> Settings:
    """Explicit kwargs, so a developer's AGRIVISION_* env vars can't change results."""
    return Settings(
        llm_enabled=True,
        llm_provider="fake",
        llm_confidence_threshold=0.60,
        llm_default_language="en",
        llm_cache_enabled=True,
        llm_cache_ttl_seconds=3600,
        llm_cache_max_entries=64,
        llm_confidence_bucket_size=10,
    )


@pytest.fixture
def provider() -> FakeProvider:
    """
    Returns VALID_REPORT rather than the provider's own built-in sample, so
    assertions here are against a report this test suite controls. A
    single-entry script repeats indefinitely, so repeat calls still work.
    """
    return FakeProvider([report_json()])


@pytest.fixture
def make_service(settings):
    """Builds a ReportService around a given provider, each with a fresh cache."""

    def _build(provider: FakeProvider, **settings_overrides) -> ReportService:
        effective = settings.model_copy(update=settings_overrides) if settings_overrides else settings
        return ReportService(
            settings=effective,
            provider=provider,
            cache=InMemoryTTLCache(
                ttl_seconds=effective.llm_cache_ttl_seconds,
                max_entries=effective.llm_cache_max_entries,
            ),
        )

    return _build


@pytest.fixture
def service(provider, make_service) -> ReportService:
    return make_service(provider)


@pytest.fixture
def client_for():
    """Builds a TestClient wired to a specific ReportService."""
    from backend.app import app

    def _build(service: ReportService) -> TestClient:
        app.dependency_overrides[get_report_service] = lambda: service
        return TestClient(app)

    yield _build
    app.dependency_overrides.clear()


@pytest.fixture
def client(service, client_for):
    """TestClient with the report service swapped for the fake-backed one."""
    return client_for(service)
