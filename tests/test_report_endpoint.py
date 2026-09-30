"""
tests/test_report_endpoint.py

POST /report through the real FastAPI stack, checking that each typed exception
reaches the client as the right status code and error body.
"""

from __future__ import annotations

from backend.services.llm.fake import FakeProvider
from backend.utils.exceptions import (
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from tests.conftest import report_json

PAYLOAD = {
    "predicted_class": "Tomato___Late_blight",
    "confidence": 0.9821,
    "top_k": [
        {"class_name": "Tomato___Late_blight", "confidence": 0.9821},
        {"class_name": "Tomato___Early_blight", "confidence": 0.0112},
    ],
}


def test_report_endpoint_returns_a_report(client):
    response = client.post("/report", json=PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["cached"] is False
    assert body["provider"] == "fake"
    assert body["prompt_version"]
    assert body["generation_time_ms"] >= 0
    assert body["report"]["disease_name"] == "Late blight"
    assert body["report"]["is_low_confidence"] is False


def test_repeat_request_is_served_from_cache(client):
    client.post("/report", json=PAYLOAD)
    response = client.post("/report", json=PAYLOAD)

    assert response.json()["cached"] is True


def test_low_confidence_request_is_hedged(client):
    response = client.post("/report", json={**PAYLOAD, "confidence": 0.31})

    assert response.status_code == 200
    report = response.json()["report"]
    assert report["is_low_confidence"] is True
    assert report["possible_alternatives"] == ["Tomato - Early blight"]


def test_invalid_confidence_is_rejected(client):
    response = client.post("/report", json={**PAYLOAD, "confidence": 1.5})

    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"


def test_empty_top_k_is_rejected(client):
    response = client.post("/report", json={**PAYLOAD, "top_k": []})

    assert response.status_code == 422


def test_provider_failure_returns_502(make_service, client_for):
    client = client_for(make_service(FakeProvider([LLMProviderError("upstream exploded")])))

    response = client.post("/report", json=PAYLOAD)

    assert response.status_code == 502
    body = response.json()
    assert body["success"] is False
    assert body["error"] == "llm_provider_error"


def test_rate_limit_returns_429(make_service, client_for):
    client = client_for(make_service(FakeProvider([LLMRateLimitError("slow down")])))

    response = client.post("/report", json=PAYLOAD)

    assert response.status_code == 429
    assert response.json()["error"] == "llm_rate_limited"


def test_timeout_returns_504(make_service, client_for):
    client = client_for(make_service(FakeProvider([LLMTimeoutError("took too long")])))

    response = client.post("/report", json=PAYLOAD)

    assert response.status_code == 504
    assert response.json()["error"] == "llm_timeout"


def test_unparseable_output_returns_502(make_service, client_for):
    client = client_for(make_service(FakeProvider(["not json", "still not json"])))

    response = client.post("/report", json=PAYLOAD)

    assert response.status_code == 502
    assert response.json()["error"] == "report_parse_error"


def test_disabled_layer_returns_503(make_service, client_for):
    client = client_for(make_service(FakeProvider([report_json()]), llm_enabled=False))

    response = client.post("/report", json=PAYLOAD)

    assert response.status_code == 503
    assert response.json()["error"] == "report_disabled"
