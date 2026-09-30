"""
backend/api/predict.py

POST /predict -- the core inference endpoint.

Pipeline (mirrors the spec exactly):
  receive upload -> validate/decode -> preprocess -> run model -> softmax ->
  top-k -> generate Grad-CAM -> return JSON.

Each step's failure mode maps to a specific, already-defined exception
(ImageValidationError, InferenceError); the app-level exception handlers in
backend/app.py turn those into a consistent ErrorResponse, so this handler
has no try/except of its own.
"""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends, File, Query, UploadFile

from backend.api.deps import get_gradcam_service, get_inference_service, get_report_service
from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger
from backend.schemas.prediction import ClassPrediction, ErrorResponse
from backend.schemas.report import PredictWithReportResponse, ReportRequest
from backend.services.gradcam_service import GradCAMService
from backend.services.inference import InferenceService
from backend.services.preprocessing import decode_image
from backend.services.report_service import ReportService
from backend.utils.exceptions import ReportError

logger = get_logger(__name__)

router = APIRouter(tags=["prediction"])


@router.post(
    "/predict",
    response_model=PredictWithReportResponse,
    # Drops the null report/report_error keys, so a plain /predict returns
    # exactly the body it did before the report layer existed.
    response_model_exclude_none=True,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid, corrupt, empty, or oversized image."},
        500: {"model": ErrorResponse, "description": "Model or Grad-CAM inference failure."},
    },
    summary="Diagnose a crop disease from a leaf image",
    description=(
        "Accepts a single leaf image (multipart/form-data), runs it through the "
        "EfficientNet-B0 classifier, and returns the top prediction, a ranked "
        "top-K list, and a Grad-CAM heatmap explaining which regions of the leaf "
        "drove the prediction.\n\n"
        "Pass `?include_report=true` to also generate the farmer-friendly LLM report "
        "in the same round trip. If report generation fails, the prediction is still "
        "returned, with the reason in `report_error`."
    ),
)
async def predict(
    image: UploadFile = File(..., description="Leaf image file (JPEG, PNG, etc.), max 10MB."),
    include_report: bool = Query(
        False, description="Also generate the farmer-friendly report for this prediction."
    ),
    language: str | None = Query(
        None, description="Report language code, e.g. 'en'. Ignored unless include_report is true."
    ),
    inference_service: InferenceService = Depends(get_inference_service),
    gradcam_service: GradCAMService = Depends(get_gradcam_service),
    report_service: ReportService = Depends(get_report_service),
    settings: Settings = Depends(get_settings),
) -> PredictWithReportResponse:
    start = time.perf_counter()

    file_bytes = await image.read()
    pil_image = decode_image(file_bytes)

    preprocessor = inference_service.preprocessor
    input_tensor = preprocessor.to_tensor(pil_image)
    display_array = preprocessor.to_display_array(pil_image)

    result = inference_service.predict(input_tensor)

    if result.confidence < settings.confidence_threshold:
        logger.warning(
            "Low-confidence prediction: %s (%.4f) below threshold %.4f",
            result.class_name, result.confidence, settings.confidence_threshold,
        )

    heatmap = gradcam_service.generate_heatmap(
        result.input_tensor, display_array, result.pred_class_idx
    )

    top_predictions = [
        ClassPrediction(class_name=score.class_name, confidence=score.confidence)
        for score in result.top_k
    ]

    report = None
    report_error = None
    if include_report:
        try:
            generated = await report_service.generate(
                ReportRequest(
                    predicted_class=result.class_name,
                    confidence=result.confidence,
                    top_k=top_predictions,
                    language=language,
                )
            )
            report = generated.report
        except ReportError as exc:
            # A diagnosis is still worth returning without advice attached, so the
            # report layer is never allowed to fail the prediction it decorates.
            logger.warning("Report generation failed for %s: %s", image.filename, exc)
            report_error = str(exc)

    processing_time_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "predict: file=%s prediction=%s confidence=%.4f report=%s total_time_ms=%.1f",
        image.filename, result.class_name, result.confidence, include_report, processing_time_ms,
    )

    return PredictWithReportResponse(
        prediction=result.class_name,
        confidence=result.confidence,
        top_predictions=top_predictions,
        heatmap=heatmap,
        processing_time_ms=processing_time_ms,
        report=report,
        report_error=report_error,
    )
