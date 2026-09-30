"""
backend/schemas/report.py

Pydantic models for the LLM report layer: the schema the LLM's JSON output is
validated against (ReportSchema), the POST /report request body, and the
response wrapper carrying cache/provider provenance alongside the report.

ReportSchema serves double duty -- its JSON schema is embedded in the prompt as
the required output shape, and it validates what actually comes back, so a
malformed or half-hallucinated response is rejected before it reaches a farmer.

PredictWithReportResponse lives here rather than in prediction.py because it
needs both ReportSchema and PredictResponse; putting it in prediction.py would
make the two schema modules import each other.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.prediction import ClassPrediction, PredictResponse


class Severity(str, Enum):
    """How urgently the farmer needs to act."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TreatmentOptions(BaseModel):
    """
    Treatment split by approach, so a farmer who can't access or afford chemical
    inputs still gets an actionable answer from the organic list.
    """

    organic: list[str] = Field(
        default_factory=list, description="Non-chemical / cultural treatment steps."
    )
    chemical: list[str] = Field(
        default_factory=list,
        description=(
            "Chemical treatment approaches, described by active-ingredient class only "
            "-- never brand names or dosages, which require a local expert."
        ),
    )


class ReportSchema(BaseModel):
    """The farmer-facing report. Every field here is produced by the LLM except
    `is_low_confidence` and `possible_alternatives`, which the server stamps."""

    disease_name: str = Field(..., description="Human-readable disease name, e.g. 'Late blight'.")
    crop: str = Field(..., description="Human-readable crop name, e.g. 'Tomato'.")
    summary: str = Field(..., description="Plain-language explanation of what is happening to the plant.")
    severity: Severity = Field(..., description="Urgency of action required.")
    severity_reason: str = Field(..., description="One short sentence justifying the severity rating.")
    symptoms_to_check: list[str] = Field(
        ..., min_length=1, description="Observable signs the farmer can verify on the plant themselves."
    )
    treatment: TreatmentOptions = Field(..., description="Organic and chemical treatment options.")
    prevention: list[str] = Field(
        ..., min_length=1, description="Practices that reduce the chance of recurrence next season."
    )
    when_to_consult_expert: str = Field(
        ..., description="The conditions under which the farmer should contact an agricultural extension officer."
    )
    confidence_note: str = Field(
        ..., description="Honest caveat about how certain this diagnosis is and what could change it."
    )

    # -- Server-stamped, never taken from the LLM --
    is_low_confidence: bool = Field(
        False,
        description=(
            "True when the prediction fell below the configured confidence threshold, "
            "meaning this report is explicitly not a definitive diagnosis."
        ),
    )
    possible_alternatives: list[str] = Field(
        default_factory=list,
        description="Other candidate diseases from the model's top-k, populated on low-confidence reports.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "disease_name": "Late blight",
                "crop": "Tomato",
                "summary": "A fast-spreading fungal disease that rots leaves and fruit in cool, wet weather.",
                "severity": "high",
                "severity_reason": "Late blight can destroy an entire tomato crop within one to two weeks.",
                "symptoms_to_check": [
                    "Dark brown patches on leaves, often with a pale green edge",
                    "White fuzzy growth on the underside of leaves in humid mornings",
                ],
                "treatment": {
                    "organic": [
                        "Remove and destroy affected leaves and fruit away from the field",
                        "Improve airflow by widening spacing between plants",
                    ],
                    "chemical": [
                        "Copper-based protectant sprays are commonly used for this disease",
                    ],
                },
                "prevention": [
                    "Avoid overhead watering late in the day",
                    "Rotate to a non-tomato, non-potato crop next season",
                ],
                "when_to_consult_expert": (
                    "Contact your local agricultural extension officer before applying any chemical "
                    "spray, and immediately if more than a few plants are affected."
                ),
                "confidence_note": "The model was highly confident, but confirm the symptoms above before treating.",
                "is_low_confidence": False,
                "possible_alternatives": [],
            }
        }
    )


class ReportRequest(BaseModel):
    """Request body for POST /report."""

    predicted_class: str = Field(
        ..., description="Model class name, in the dataset's `Crop___Disease` folder format."
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Top-1 softmax confidence.")
    top_k: list[ClassPrediction] = Field(
        ..., min_length=1, description="Top-K predictions ranked by confidence, descending."
    )
    language: str | None = Field(
        None, description="Output language code, e.g. 'en'. Falls back to the configured default."
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "predicted_class": "Tomato___Late_blight",
                "confidence": 0.9821,
                "top_k": [
                    {"class_name": "Tomato___Late_blight", "confidence": 0.9821},
                    {"class_name": "Tomato___Early_blight", "confidence": 0.0112},
                ],
                "language": "en",
            }
        }
    )


class ReportResponse(BaseModel):
    """Successful response body for POST /report."""

    success: bool = Field(True, description="Always true on this model; failures use ErrorResponse instead.")
    report: ReportSchema = Field(..., description="The generated farmer-facing report.")
    cached: bool = Field(..., description="True if served from cache without calling the LLM.")
    provider: str = Field(..., description="LLM provider that produced the report, e.g. 'gemini'.")
    prompt_version: str = Field(..., description="Version of the prompt template used.")
    generation_time_ms: float = Field(..., ge=0.0, description="Server-side time to produce the report.")


class PredictWithReportResponse(PredictResponse):
    """
    Response for POST /predict, extended with the optional report.

    Both added fields default to None and the route sets
    `response_model_exclude_none=True`, so a plain /predict call returns exactly
    the body it did before this layer existed.
    """

    report: ReportSchema | None = Field(
        None, description="Present when ?include_report=true and generation succeeded."
    )
    report_error: str | None = Field(
        None,
        description=(
            "Present when ?include_report=true and generation failed. The prediction itself "
            "still succeeds -- the LLM layer is never allowed to fail a diagnosis."
        ),
    )
