"""
tests/test_report_cache.py

The cache key carries a correctness requirement, not just a performance one:
two predictions that would produce different advice must never collide.
"""

from __future__ import annotations

from backend.schemas.report import ReportSchema
from backend.services.report_cache import (
    InMemoryTTLCache,
    NullCache,
    build_cache,
    build_cache_key,
)
from tests.conftest import VALID_REPORT

REPORT = ReportSchema.model_validate(VALID_REPORT)

KEY_ARGS = {
    "predicted_class": "Tomato___Late_blight",
    "language": "en",
    "top_k_class_names": ["Tomato___Late_blight", "Tomato___Early_blight"],
    "bucket_size": 10,
}


async def test_set_then_get_roundtrip():
    cache = InMemoryTTLCache(ttl_seconds=60, max_entries=8)
    await cache.set("k", REPORT)

    assert await cache.get("k") == REPORT


async def test_missing_key_returns_none():
    cache = InMemoryTTLCache(ttl_seconds=60, max_entries=8)

    assert await cache.get("absent") is None


async def test_expired_entry_is_dropped():
    # Negative TTL expires the entry before it can ever be read, which makes the
    # test deterministic rather than dependent on a real clock tick.
    cache = InMemoryTTLCache(ttl_seconds=-1, max_entries=8)
    await cache.set("k", REPORT)

    assert await cache.get("k") is None
    assert "k" not in cache._entries


async def test_oldest_entry_is_evicted_at_capacity():
    cache = InMemoryTTLCache(ttl_seconds=60, max_entries=2)
    await cache.set("first", REPORT)
    await cache.set("second", REPORT)
    await cache.set("third", REPORT)

    assert await cache.get("first") is None
    assert await cache.get("second") is not None
    assert await cache.get("third") is not None


async def test_null_cache_never_stores():
    cache = NullCache()
    await cache.set("k", REPORT)

    assert await cache.get("k") is None


def test_build_cache_returns_null_when_disabled():
    assert isinstance(build_cache(enabled=False, ttl_seconds=60, max_entries=8), NullCache)
    assert isinstance(build_cache(enabled=True, ttl_seconds=60, max_entries=8), InMemoryTTLCache)


def test_confidences_in_same_bucket_share_a_key():
    assert build_cache_key(confidence=0.912, **KEY_ARGS) == build_cache_key(
        confidence=0.954, **KEY_ARGS
    )


def test_confidences_in_different_buckets_differ():
    assert build_cache_key(confidence=0.912, **KEY_ARGS) != build_cache_key(
        confidence=0.412, **KEY_ARGS
    )


def test_language_changes_the_key():
    args = {**KEY_ARGS, "language": "hi"}
    assert build_cache_key(confidence=0.9, **KEY_ARGS) != build_cache_key(confidence=0.9, **args)


def test_different_runner_up_changes_the_key():
    """
    Hedged reports name the runner-up candidates in their text, so a differing
    top-k must not reuse a cached report that lists the wrong alternatives.
    """
    args = {**KEY_ARGS, "top_k_class_names": ["Tomato___Late_blight", "Tomato___Leaf_Mold"]}
    assert build_cache_key(confidence=0.4, **KEY_ARGS) != build_cache_key(confidence=0.4, **args)
