"""
tests/test_cors.py

CORS: only configured origins get an Access-Control-Allow-Origin header,
credentials are never allowed, and the origin list can be set from the
environment as a JSON list.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app import create_app
from backend.core.config import Settings

FRONTEND = "http://localhost:3000"


def _client(origins: list[str]) -> TestClient:
    return TestClient(create_app(Settings(cors_origins=origins)))


def _preflight(client: TestClient, origin: str):
    return client.options(
        "/predict",
        headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
    )


def test_default_origin_is_the_local_frontend_not_a_wildcard(monkeypatch):
    monkeypatch.delenv("AGRIVISION_CORS_ORIGINS", raising=False)

    assert Settings().cors_origins == [FRONTEND]


def test_allowed_origin_passes_preflight():
    response = _preflight(_client([FRONTEND]), FRONTEND)

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == FRONTEND
    assert "access-control-allow-credentials" not in response.headers


def test_other_origin_gets_no_cors_headers():
    response = _client([FRONTEND]).get("/", headers={"Origin": "https://evil.example"})

    assert "access-control-allow-origin" not in response.headers


def test_origins_load_from_env_as_json(monkeypatch):
    monkeypatch.setenv("AGRIVISION_CORS_ORIGINS", '["https://a.example", "https://b.example"]')

    assert Settings.from_yaml().cors_origins == ["https://a.example", "https://b.example"]


def test_origins_load_from_yaml_when_env_unset(monkeypatch):
    monkeypatch.delenv("AGRIVISION_CORS_ORIGINS", raising=False)

    assert Settings.from_yaml().cors_origins == [FRONTEND]
