"""
backend/schemas/prediction.py

Pydantic response models for POST /predict.

Declared as FastAPI's `response_model` for the endpoint, so:
  - Swagger/OpenAPI docs are generated automatically with types + examples.
  - FastAPI validates and serializes the service layer's return value,
    catching a malformed response (e.g. a confidence > 1.0 from a bug)
    before it ever reaches a client.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Every `error` value the API can return: the error_code of each
# AgriVisionError subclass, plus the two the app-level handlers emit directly.
# A literal rather than a free string so the OpenAPI schema (and the frontend
# types generated from it) enumerate them; tests/test_error_codes.py fails if
# an exception class is added without being listed here.
ErrorCode = Literal[
    "invalid_image",
    "image_too_large",
    "unsupported_image_type",
    "invalid_feedback",
    "inference_error",
    "report_error",
    "report_disabled",
    "llm_configuration_error",
    "llm_provider_error",
    "llm_timeout",
    "llm_rate_limited",
    "report_parse_error",
    "validation_error",
    "internal_error",
]


class ClassPrediction(BaseModel):
    """A single (class, confidence) pair, used for the top-k ranked list."""

    class_name: str = Field(..., description="Predicted disease class name.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Softmax probability for this class.")

    model_config = ConfigDict(
        json_schema_extra={"example": {"class_name": "Tomato___Late_blight", "confidence": 0.9821}}
    )


class PredictResponse(BaseModel):
    """Successful response body for POST /predict."""

    success: bool = Field(True, description="Always true on this model; failures use ErrorResponse instead.")
    prediction: str = Field(..., description="Top-1 predicted class name.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence of the top-1 prediction.")
    is_low_confidence: bool = Field(
        ...,
        description=(
            "True when the top-1 confidence is below the configured threshold, i.e. the "
            "prediction is too uncertain to present as a diagnosis. Same rule the report "
            "layer uses to switch to its non-definitive variant."
        ),
    )
    top_predictions: list[ClassPrediction] = Field(
        ..., min_length=1, description="Top-K predictions ranked by confidence, descending."
    )
    heatmap: str = Field(
        ...,
        description="Grad-CAM overlay as a base64-encoded PNG data URI (`data:image/png;base64,...`).",
    )
    processing_time_ms: float = Field(
        ..., ge=0.0, description="End-to-end server-side processing time, in milliseconds."
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "prediction": "Tomato___Late_blight",
                "confidence": 0.9821,
                "is_low_confidence": False,
                "top_predictions": [
                    {"class_name": "Tomato___Late_blight", "confidence": 0.9821},
                    {"class_name": "Tomato___Early_blight", "confidence": 0.0112},
                    {"class_name": "Tomato___healthy", "confidence": 0.0041},
                ],
                "heatmap": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
                "processing_time_ms": 42.7,
            }
        }
    )


class ErrorResponse(BaseModel):
    """Uniform error body for every 4xx/5xx the API returns."""

    success: bool = Field(False, description="Always false on this model.")
    error: ErrorCode = Field(..., description="Short machine-readable error code, e.g. 'invalid_image'.")
    detail: str = Field(..., description="Human-readable explanation of what went wrong.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": "invalid_image",
                "detail": "Uploaded file is not a valid image (failed to decode).",
            }
        }
    )
