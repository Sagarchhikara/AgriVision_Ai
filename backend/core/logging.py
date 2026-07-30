"""
backend/core/logging.py

Central logging setup for the backend. Every module gets its logger via
get_logger(__name__) instead of calling print(), so output is timestamped,
leveled, and captured in a rotating log file in addition to the console.

setup_logging() is idempotent — calling it more than once (e.g. once from
app.py's startup and again from a test fixture) will not duplicate handlers.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOGGER_NAME = "agrivision"
_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_configured = False


def setup_logging(log_level: str = "INFO", log_file: Path | str | None = None) -> None:
    """Configure the shared 'agrivision' logger. Safe to call multiple times."""
    global _configured
    logger = logging.getLogger(_LOGGER_NAME)

    if _configured:
        logger.setLevel(log_level.upper())
        return

    logger.setLevel(log_level.upper())
    formatter = logging.Formatter(_LOG_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file is not None:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_path, maxBytes=5 * 1024 * 1024, backupCount=3
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.propagate = False
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Return a child of the shared 'agrivision' logger, namespaced by module.

    If setup_logging() hasn't run yet (e.g. a unit test importing a service
    directly, bypassing app startup), falls back to a basic console-only
    configuration so log calls never silently disappear or raise.
    """
    if not _configured:
        setup_logging()
    return logging.getLogger(_LOGGER_NAME).getChild(name)
