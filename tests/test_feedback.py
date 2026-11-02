"""
tests/test_feedback.py

POST /feedback: valid verdicts are appended as JSON lines under the feedback
directory; contradictory or unknown-class feedback is rejected before anything
is written.
"""

from __future__ import annotations

import json

FEEDBACK = {
    "predicted_class": "Tomato___Late_blight",
    "confidence": 0.81,
    "top_k": [
        {"class_name": "Tomato___Late_blight", "confidence": 0.81},
        {"class_name": "Tomato___Early_blight", "confidence": 0.15},
    ],
    "verdict": "no",
    "correct_class": "Tomato___Early_blight",
    "language": "hi",
}


def _records(feedback_dir) -> list[dict]:
    lines = []
    for path in sorted(feedback_dir.glob("feedback-*.jsonl")):
        lines.extend(path.read_text(encoding="utf-8").splitlines())
    return [json.loads(line) for line in lines]


def test_feedback_is_appended_as_a_json_line(make_api_client, feedback_dir):
    response = make_api_client().post("/feedback", json=FEEDBACK)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True

    [record] = _records(feedback_dir)
    assert record["id"] == body["feedback_id"]
    assert record["received_at"]
    assert record["app_version"] == "test"
    assert {key: record[key] for key in FEEDBACK} == FEEDBACK


def test_each_submission_adds_one_line(make_api_client, feedback_dir):
    client = make_api_client()

    client.post("/feedback", json=FEEDBACK)
    client.post("/feedback", json={**FEEDBACK, "verdict": "unsure", "correct_class": None})

    assert [r["verdict"] for r in _records(feedback_dir)] == ["no", "unsure"]


def test_yes_without_a_correct_class_is_accepted(make_api_client, feedback_dir):
    payload = {**FEEDBACK, "verdict": "yes"}
    del payload["correct_class"]

    assert make_api_client().post("/feedback", json=payload).status_code == 200
    assert _records(feedback_dir)[0]["correct_class"] is None


def test_yes_with_a_correct_class_is_rejected(make_api_client, feedback_dir):
    response = make_api_client().post("/feedback", json={**FEEDBACK, "verdict": "yes"})

    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"
    assert _records(feedback_dir) == []


def test_unknown_verdict_is_rejected(make_api_client):
    response = make_api_client().post("/feedback", json={**FEEDBACK, "verdict": "maybe"})

    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"


def test_unknown_class_name_is_rejected(make_api_client, feedback_dir):
    for field, payload in (
        ("predicted_class", {**FEEDBACK, "predicted_class": "Banana___Panama"}),
        ("correct_class", {**FEEDBACK, "correct_class": "Banana___Panama"}),
        ("top_k", {**FEEDBACK, "top_k": [{"class_name": "Banana___Panama", "confidence": 0.81}]}),
    ):
        response = make_api_client().post("/feedback", json=payload)

        assert response.status_code == 422, field
        body = response.json()
        assert body["error"] == "invalid_feedback"
        assert "Banana___Panama" in body["detail"]

    assert _records(feedback_dir) == []
