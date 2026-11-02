"""
backend/services/feedback_store.py

Appends user feedback to a local JSON Lines file -- the MVP stand-in for a
database. One file per UTC day (feedback-YYYY-MM-DD.jsonl) keeps any single
file small and makes "last week's feedback" a glob rather than a scan.

Each record is written with a single write() call on a file opened in append
mode, under a lock, so concurrent requests in this process can't interleave
lines. Multiple worker processes writing the same file rely on O_APPEND, which
is fine for lines this small on a local filesystem but is the first thing to
replace (with a real database) once this needs to scale.
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from backend.core.logging import get_logger
from backend.schemas.feedback import FeedbackRequest

logger = get_logger(__name__)


class FeedbackStore:
    def __init__(self, directory: Path, app_version: str):
        self.directory = directory
        self.app_version = app_version
        self._lock = threading.Lock()

    def append(self, feedback: FeedbackRequest) -> str:
        """Persist one feedback record and return its generated ID."""
        received_at = datetime.now(timezone.utc)
        feedback_id = uuid.uuid4().hex
        record = {
            "id": feedback_id,
            "received_at": received_at.isoformat(),
            "app_version": self.app_version,
            **feedback.model_dump(),
        }
        line = json.dumps(record, ensure_ascii=False) + "\n"
        path = self.directory / f"feedback-{received_at:%Y-%m-%d}.jsonl"

        with self._lock:
            self.directory.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(line)

        logger.info(
            "feedback: id=%s predicted=%s verdict=%s correct_class=%s",
            feedback_id, feedback.predicted_class, feedback.verdict, feedback.correct_class,
        )
        return feedback_id
