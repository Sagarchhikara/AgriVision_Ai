"""
backend/schemas/feedback.py

Request/response models for POST /feedback: a farmer's verdict on whether a
diagnosis was right.

The prediction is sent back by value rather than referenced by an ID, since
/predict is stateless and keeps no record of what it returned. No image is
accepted or stored.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.schemas.prediction import ClassPrediction
from backend.schemas.report import SupportedLanguage

FeedbackVerdict = Literal["yes", "no", "unsure"]


class FeedbackRequest(BaseModel):
    """Request body for POST /feedback."""

    predicted_class: str = Field(..., description="Top-1 class the user was shown.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Top-1 confidence the user was shown.")
    top_k: list[ClassPrediction] = Field(
        ..., min_length=1, description="Top-K predictions the user was shown, descending."
    )
    verdict: FeedbackVerdict = Field(..., description="Whether the user believes the diagnosis was correct.")
    correct_class: str | None = Field(
        None,
        description=(
            "The class the user believes is correct, if they know it. "
            "Only allowed when verdict is 'no' or 'unsure'."
        ),
    )
    language: SupportedLanguage | None = Field(None, description="UI language the user was using.")

    @model_validator(mode="after")
    def _correct_class_contradicts_yes(self) -> "FeedbackRequest":
        if self.verdict == "yes" and self.correct_class is not None:
            raise ValueError("correct_class must be omitted when verdict is 'yes'.")
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "predicted_class": "Potato___Late_blight",
                "confidence": 0.81,
                "top_k": [
                    {"class_name": "Potato___Late_blight", "confidence": 0.81},
                    {"class_name": "Potato___Early_blight", "confidence": 0.15},
                ],
                "verdict": "no",
                "correct_class": "Potato___Early_blight",
                "language": "hi",
            }
        }
    )


class FeedbackResponse(BaseModel):
    """Successful response body for POST /feedback."""

    success: bool = Field(True, description="Always true on this model; failures use ErrorResponse instead.")
    feedback_id: str = Field(..., description="Server-assigned ID of the stored feedback record.")
