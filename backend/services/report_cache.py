"""
backend/services/report_cache.py

Caching for generated reports, keyed so that identical diagnoses reuse one LLM
call instead of paying for the same advice repeatedly.

Design notes
------------
- The key includes a signature of the top-k class names, not just the top-1
  class. Low-confidence reports name the runner-up candidates in their text, so
  two predictions sharing a top-1 but differing in their runners-up must not
  share a cached report -- it would list the wrong alternatives.
- Confidence is bucketed rather than used exactly: 0.9612 and 0.9598 deserve
  the same advice, and an exact-match key would make the cache useless since
  softmax outputs are effectively unique per image.
- get/set are async purely so a Redis-backed implementation can slot in behind
  the same protocol without touching a single call site.
- No lock around the dict: the event loop is single-threaded and neither method
  awaits between reading and mutating, so there is no interleaving to guard.
  Two concurrent misses for the same key can both call the LLM, which wastes one
  call but cannot corrupt anything.
"""

from __future__ import annotations

import time
from typing import Protocol

from backend.core.logging import get_logger
from backend.schemas.report import ReportSchema

logger = get_logger(__name__)


def build_cache_key(
    predicted_class: str,
    confidence: float,
    language: str,
    top_k_class_names: list[str],
    bucket_size: int,
) -> str:
    """
    Build the cache key for one report.

    Args:
        bucket_size: confidence bucket width in percentage points, e.g. 10 puts
            every confidence in the same decile into one bucket.
    """
    bucket = int(confidence * 100) // bucket_size
    candidates = "|".join(top_k_class_names)
    return f"{predicted_class}::{bucket}::{language}::{candidates}"


class ReportCache(Protocol):
    """Storage for generated reports. Implement this to back it with Redis."""

    async def get(self, key: str) -> ReportSchema | None: ...

    async def set(self, key: str, report: ReportSchema) -> None: ...


class InMemoryTTLCache:
    """Process-local cache with per-entry expiry and a bounded entry count."""

    def __init__(self, ttl_seconds: int, max_entries: int):
        self._ttl = ttl_seconds
        self._max_entries = max_entries
        self._entries: dict[str, tuple[float, ReportSchema]] = {}

    async def get(self, key: str) -> ReportSchema | None:
        entry = self._entries.get(key)
        if entry is None:
            return None

        expires_at, report = entry
        if time.monotonic() >= expires_at:
            del self._entries[key]
            return None
        return report

    async def set(self, key: str, report: ReportSchema) -> None:
        if len(self._entries) >= self._max_entries and key not in self._entries:
            # Evict the oldest insertion; dicts preserve insertion order.
            oldest = next(iter(self._entries))
            del self._entries[oldest]
        self._entries[key] = (time.monotonic() + self._ttl, report)


class NullCache:
    """No-op cache used when caching is disabled, so callers need no branch."""

    async def get(self, key: str) -> ReportSchema | None:
        return None

    async def set(self, key: str, report: ReportSchema) -> None:
        return None


def build_cache(enabled: bool, ttl_seconds: int, max_entries: int) -> ReportCache:
    """Return the configured cache implementation."""
    if not enabled:
        logger.info("Report caching disabled; every request will call the LLM.")
        return NullCache()
    return InMemoryTTLCache(ttl_seconds=ttl_seconds, max_entries=max_entries)
