"""
backend/api/feedback.py

POST /feedback -- records whether a user believes a diagnosis was correct.

The model is far less accurate on field photos than on lab images, so these
verdicts are the cheapest available signal about real-world accuracy per
class. Records go to JSON Lines under outputs/feedback/ (see FeedbackStore);
no image is stored.

A plain `def` rather than `async def`: the handler does blocking file I/O, so
FastAPI runs it in its threadpool instead of on the event loop.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.deps import get_feedback_store, get_inference_service
from backend.schemas.feedback import FeedbackRequest, FeedbackResponse
from backend.schemas.prediction import ErrorResponse
from backend.services.feedback_store import FeedbackStore
from backend.services.inference import InferenceService
from backend.utils.exceptions import InvalidFeedbackError

router = APIRouter(tags=["feedback"])


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    responses={
        422: {"model": ErrorResponse, "description": "Malformed feedback, or a class name the model does not know."},
    },
    summary="Record whether a diagnosis was correct",
    description=(
        "Stores the user's verdict (yes / no / unsure) on a prediction, optionally with "
        "the class they believe is correct. The prediction is sent back by value, since "
        "/predict keeps no record of what it returned. No image is stored."
    ),
)
def submit_feedback(
    payload: FeedbackRequest,
    inference_service: InferenceService = Depends(get_inference_service),
    feedback_store: FeedbackStore = Depends(get_feedback_store),
) -> FeedbackResponse:
    named = {payload.predicted_class, *(item.class_name for item in payload.top_k)}
    if payload.correct_class is not None:
        named.add(payload.correct_class)

    unknown = sorted(named - set(inference_service.class_names))
    if unknown:
        raise InvalidFeedbackError(f"Unknown class name(s): {', '.join(unknown)}.")

    return FeedbackResponse(feedback_id=feedback_store.append(payload))
