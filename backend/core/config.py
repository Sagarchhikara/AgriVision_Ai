"""
backend/core/config.py

Centralized backend configuration.

Loads configs/config.yaml — the same file the training pipeline uses — and
layers pydantic-settings on top so that:

  - ML-pipeline-shared values (image size, dataset root, model architecture)
    have exactly one source of truth between training and serving; they are
    read from configs/config.yaml's existing `training`/`dataset`/`model`
    sections instead of being duplicated.
  - Deployment-specific values (host, port, log level, ...) can be overridden
    per-environment with `AGRIVISION_*` environment variables without editing
    YAML (e.g. `AGRIVISION_PORT=9000`), which is what you want in Docker/K8s.

Precedence for every field is: environment variable > configs/config.yaml
`backend` section > field default below.

get_settings() is lru_cache'd: the YAML file is parsed and validated exactly
once per process and the same Settings instance is reused everywhere
(including as a FastAPI dependency), mirroring "load the model only once".
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "config.yaml"

_ENV_PREFIX = "AGRIVISION_"

# Load .env into the real environment before anything reads it. This has to
# happen here rather than via pydantic-settings' env_file, because provider API
# keys are read straight from os.environ in the LLM factory and would never
# reach a Settings field. override=False keeps a real exported variable winning
# over the file, which is what you want when overriding a key at deploy time.
for _env_file in (PROJECT_ROOT / ".env", PROJECT_ROOT / "backend" / ".env"):
    load_dotenv(_env_file, override=False)


def _load_yaml(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"Backend config file not found: {path}")
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


class Settings(BaseSettings):
    """Resolved backend configuration. Construct via `Settings.from_yaml()`."""

    model_config = SettingsConfigDict(env_prefix=_ENV_PREFIX, extra="ignore")

    # -- App metadata --
    app_name: str = "AgriVision_Ai Inference API"
    app_version: str = "0.1.0"

    # -- Model / checkpoint (shared with training config.yaml) --
    model_name: str = "efficientnet_b0"
    model_pretrained: bool = True
    checkpoint_path: Path = PROJECT_ROOT / "outputs" / "checkpoints" / "best.pt"
    image_size: int = 224

    # -- Class names are derived from this split's folder listing at startup
    # (ImageFolder's alphabetical ordering), since the checkpoint itself does
    # not store class names. Must match the split used to train `best.pt`.
    dataset_root: Path = PROJECT_ROOT / "datasets"
    class_names_split: str = "train"

    # -- Inference behavior --
    top_k: int = 3
    confidence_threshold: float = 0.0
    device: Literal["auto", "cuda", "mps", "cpu"] = "auto"

    # -- Server --
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    # -- Logging --
    log_level: str = "INFO"
    log_file: Path = PROJECT_ROOT / "outputs" / "logs" / "backend.log"

    # -- LLM report layer --
    # Defaults to the 'fake' provider so the backend runs with no API keys at
    # all; selecting gemini/openai is a deliberate act that then requires a key.
    llm_enabled: bool = True
    llm_provider: Literal["fake", "gemini", "openai"] = "fake"
    llm_model: str = "gemini-2.0-flash"
    llm_timeout_seconds: float = 30.0
    llm_max_output_tokens: int = 1200
    llm_temperature: float = 0.3
    llm_confidence_threshold: float = Field(0.60, ge=0.0, le=1.0)
    llm_default_language: str = "en"
    llm_cache_enabled: bool = True
    llm_cache_ttl_seconds: int = 86400
    llm_cache_max_entries: int = 512
    llm_confidence_bucket_size: int = Field(10, ge=1, le=100)

    @field_validator("checkpoint_path", "dataset_root", "log_file", mode="before")
    @classmethod
    def _resolve_relative_to_project_root(cls, value: str | Path) -> Path:
        """configs/config.yaml paths are written relative to the repo root,
        not to whatever directory the server happens to be launched from."""
        path = Path(value)
        return path if path.is_absolute() else PROJECT_ROOT / path

    @staticmethod
    def _env_override_present(field_name: str) -> bool:
        return f"{_ENV_PREFIX}{field_name.upper()}" in os.environ

    @classmethod
    def from_yaml(cls, config_path: Path = DEFAULT_CONFIG_PATH) -> "Settings":
        """
        Build Settings from configs/config.yaml, respecting env var precedence.

        Only fields *not* already set via an AGRIVISION_* environment variable
        are taken from YAML, so an operator can override a single value at
        deploy time without forking the config file.
        """
        raw = _load_yaml(config_path)
        overrides: dict = {}

        def maybe_set(field_name: str, value) -> None:
            if not cls._env_override_present(field_name):
                overrides[field_name] = value

        model_section = raw.get("model", {})
        if "name" in model_section:
            maybe_set("model_name", model_section["name"])
        if "pretrained" in model_section:
            maybe_set("model_pretrained", model_section["pretrained"])

        training_section = raw.get("training", {})
        if "image_size" in training_section:
            maybe_set("image_size", training_section["image_size"])

        dataset_section = raw.get("dataset", {})
        if "root" in dataset_section:
            maybe_set("dataset_root", dataset_section["root"])

        backend_section = raw.get("backend", {})
        for key in (
            "checkpoint_path",
            "top_k",
            "confidence_threshold",
            "device",
            "host",
            "port",
            "cors_origins",
            "log_level",
            "log_file",
        ):
            if key in backend_section:
                maybe_set(key, backend_section[key])

        llm_section = raw.get("llm", {})
        if "api_key" in llm_section:
            # Deliberately ignored: a key committed to YAML is a key committed to
            # git. Uses the stdlib logger directly rather than core.logging's
            # get_logger(), which would configure logging before app startup gets
            # the chance to attach the file handler.
            logging.getLogger("agrivision.config").warning(
                "Ignoring 'llm.api_key' in %s -- API keys are read from the "
                "environment only (GEMINI_API_KEY / OPENAI_API_KEY / %sLLM_API_KEY).",
                config_path, _ENV_PREFIX,
            )
        for key in (
            "enabled",
            "provider",
            "model",
            "timeout_seconds",
            "max_output_tokens",
            "temperature",
            "confidence_threshold",
            "default_language",
        ):
            if key in llm_section:
                maybe_set(f"llm_{key}", llm_section[key])

        cache_section = llm_section.get("cache", {})
        for key in ("enabled", "ttl_seconds", "max_entries"):
            if key in cache_section:
                maybe_set(f"llm_cache_{key}", cache_section[key])
        if "confidence_bucket_size" in cache_section:
            maybe_set("llm_confidence_bucket_size", cache_section["confidence_bucket_size"])

        return cls(**overrides)


@lru_cache
def get_settings() -> Settings:
    """Process-wide singleton settings loader; use as a FastAPI dependency."""
    return Settings.from_yaml()
