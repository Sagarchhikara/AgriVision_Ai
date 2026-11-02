"""
tests/test_languages.py

The report `language` parameter is restricted to the languages the prompts
actually support, on both /report and /predict?include_report=true.
"""

from __future__ import annotations

from typing import get_args

from backend.schemas.report import SupportedLanguage
from backend.services.report_prompts import LANGUAGE_NAMES
from tests.conftest import image_upload
from tests.test_report_endpoint import PAYLOAD


def test_schema_languages_match_the_prompts():
    assert set(get_args(SupportedLanguage)) == set(LANGUAGE_NAMES)


def test_report_accepts_each_supported_language(client):
    for language in get_args(SupportedLanguage):
        response = client.post("/report", json={**PAYLOAD, "language": language})
        assert response.status_code == 200, language


def test_report_rejects_an_unsupported_language(client):
    response = client.post("/report", json={**PAYLOAD, "language": "fr"})

    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"


def test_predict_rejects_an_unsupported_language(make_api_client):
    response = make_api_client().post(
        "/predict?include_report=true&language=fr", files=image_upload()
    )

    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"
