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

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "config.yaml"

_ENV_PREFIX = "AGRIVISION_"


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

        return cls(**overrides)


@lru_cache
def get_settings() -> Settings:
    """Process-wide singleton settings loader; use as a FastAPI dependency."""
    return Settings.from_yaml()
