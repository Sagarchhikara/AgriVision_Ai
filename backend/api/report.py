"""
backend/api/report.py

POST /report -- turns a prediction into a farmer-readable report.

Takes the prediction as a request body rather than an image, so a client that
already called /predict (and has the heatmap it wants to show) can request the
report separately, and so a report can be regenerated in another language
without re-running the model.

Like the other routes, this has no try/except: every failure mode is a typed
AgriVisionError subclass that the app-level handlers in backend/app.py map to
an ErrorResponse with the right status.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.deps import get_report_service
from backend.core.logging import get_logger
from backend.schemas.prediction import ErrorResponse
from backend.schemas.report import ReportRequest, ReportResponse
from backend.services.report_service import ReportService

logger = get_logger(__name__)

router = APIRouter(tags=["report"])


@router.post(
    "/report",
    response_model=ReportResponse,
    responses={
        429: {"model": ErrorResponse, "description": "Upstream LLM rate limit hit."},
        502: {"model": ErrorResponse, "description": "LLM provider failed or returned unusable output."},
        503: {"model": ErrorResponse, "description": "Report generation is disabled on this deployment."},
        504: {"model": ErrorResponse, "description": "LLM provider timed out."},
    },
    summary="Generate a farmer-friendly report for a prediction",
    description=(
        "Turns a classifier prediction into a plain-language report: what the disease is, "
        "how urgent it is, organic and chemical treatment options, prevention, and an honest "
        "confidence caveat.\n\n"
        "When the prediction's confidence falls below the configured threshold, the response "
        "is deliberately non-definitive: `is_low_confidence` is set, `possible_alternatives` "
        "lists the other candidates, and the report asks for a better photo instead of naming "
        "a disease. The classifier is far less accurate on real field photos than on lab "
        "images, so a confident-sounding report on a weak prediction would be actively "
        "misleading."
    ),
)
async def generate_report(
    payload: ReportRequest,
    report_service: ReportService = Depends(get_report_service),
) -> ReportResponse:
    result = await report_service.generate(payload)

    logger.info(
        "report: class=%s confidence=%.4f cached=%s provider=%s time_ms=%.1f",
        payload.predicted_class, payload.confidence, result.cached,
        result.provider, result.generation_time_ms,
    )

    return ReportResponse(
        report=result.report,
        cached=result.cached,
        provider=result.provider,
        prompt_version=result.prompt_version,
        generation_time_ms=result.generation_time_ms,
    )
