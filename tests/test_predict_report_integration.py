"""
tests/test_predict_report_integration.py

The /predict + report integration, in particular the rule that the LLM layer is
never allowed to fail a diagnosis: if report generation breaks, the prediction
still comes back with the reason attached.

Inference and Grad-CAM are faked here so these tests need no checkpoint and no
GPU -- the model path itself is not what's under test.
"""

from __future__ import annotations

import io

from PIL import Image

from backend.api.deps import get_gradcam_service, get_inference_service
from backend.services.inference import ClassScore, PredictionResult
from backend.services.llm.fake import FakeProvider
from backend.utils.exceptions import LLMTimeoutError
from tests.conftest import report_json


class _FakePreprocessor:
    def to_tensor(self, image):
        return "tensor"

    def to_display_array(self, image):
        return "display-array"


class _FakeInferenceService:
    def __init__(self):
        self.preprocessor = _FakePreprocessor()

    def predict(self, input_tensor):
        return PredictionResult(
            pred_class_idx=0,
            class_name="Tomato___Late_blight",
            confidence=0.98,
            top_k=[
                ClassScore(class_name="Tomato___Late_blight", confidence=0.98),
                ClassScore(class_name="Tomato___Early_blight", confidence=0.02),
            ],
            input_tensor=input_tensor,
            inference_time_ms=1.0,
        )


class _FakeGradCAMService:
    def generate_heatmap(self, input_tensor, display_image, target_class_idx):
        return "data:image/png;base64,FAKE"


def _png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "green").save(buffer, format="PNG")
    return buffer.getvalue()


def _upload():
    return {"image": ("leaf.png", _png_bytes(), "image/png")}


def _override_model_services():
    from backend.app import app

    app.dependency_overrides[get_inference_service] = lambda: _FakeInferenceService()
    app.dependency_overrides[get_gradcam_service] = lambda: _FakeGradCAMService()


def test_plain_predict_has_no_report_fields(make_service, client_for):
    """The default response must look exactly as it did before this layer existed."""
    _override_model_services()
    client = client_for(make_service(FakeProvider([report_json()])))

    response = client.post("/predict", files=_upload())

    assert response.status_code == 200
    body = response.json()
    assert "report" not in body
    assert "report_error" not in body
    assert sorted(body) == [
        "confidence", "heatmap", "is_low_confidence", "prediction", "processing_time_ms",
        "success", "top_predictions",
    ]


def test_include_report_attaches_the_report(make_service, client_for):
    _override_model_services()
    client = client_for(make_service(FakeProvider([report_json()])))

    response = client.post("/predict?include_report=true", files=_upload())

    assert response.status_code == 200
    body = response.json()
    assert body["prediction"] == "Tomato___Late_blight"
    assert body["report"]["disease_name"] == "Late blight"
    assert "report_error" not in body


def test_prediction_survives_report_failure(make_service, client_for):
    _override_model_services()
    client = client_for(make_service(FakeProvider([LLMTimeoutError("provider took too long")])))

    response = client.post("/predict?include_report=true", files=_upload())

    assert response.status_code == 200
    body = response.json()
    assert body["prediction"] == "Tomato___Late_blight"
    assert body["heatmap"].startswith("data:image/png;base64,")
    assert "report" not in body
    assert "provider took too long" in body["report_error"]
