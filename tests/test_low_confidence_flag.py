"""
tests/test_low_confidence_flag.py

/predict's `is_low_confidence` flag, which lets a client switch to its
"uncertain result" layout before (or without) a report. It must agree with the
report layer's own flag, since both come from Settings.is_low_confidence.
"""

from __future__ import annotations

from tests.conftest import image_upload


def test_confident_prediction_is_not_flagged(make_api_client):
    body = make_api_client(confidence=0.98).post("/predict", files=image_upload()).json()

    assert body["is_low_confidence"] is False


def test_weak_prediction_is_flagged(make_api_client):
    body = make_api_client(confidence=0.41).post("/predict", files=image_upload()).json()

    assert body["is_low_confidence"] is True


def test_threshold_comes_from_settings(make_api_client):
    client = make_api_client(confidence=0.70, llm_confidence_threshold=0.80)

    assert client.post("/predict", files=image_upload()).json()["is_low_confidence"] is True


def test_flag_matches_the_report_on_both_sides_of_the_threshold(make_api_client):
    # 0.60 is the threshold itself: not below it, so not low confidence.
    for confidence in (0.59, 0.60, 0.61):
        client = make_api_client(confidence=confidence, llm_confidence_threshold=0.60)

        body = client.post("/predict?include_report=true", files=image_upload()).json()

        assert body["is_low_confidence"] is body["report"]["is_low_confidence"], confidence
        assert body["is_low_confidence"] is (confidence < 0.60)
