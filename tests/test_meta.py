"""
tests/test_meta.py

GET /meta: the class list, languages, and upload limits a client builds its UI from.
"""

from __future__ import annotations

from tests.conftest import CLASS_NAMES


def test_meta_reports_classes_languages_and_limits(make_api_client):
    response = make_api_client(max_upload_bytes=5 * 1024 * 1024).get("/meta")

    assert response.status_code == 200
    assert response.json() == {
        "classes": CLASS_NAMES,
        "languages": ["en", "hi", "pa"],
        "default_language": "en",
        "max_upload_bytes": 5 * 1024 * 1024,
        "allowed_image_types": ["image/jpeg", "image/png", "image/webp"],
    }
