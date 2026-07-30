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

from fastapi import APIRouter, Depends, File, UploadFile

from backend.api.deps import get_gradcam_service, get_inference_service
from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger
from backend.schemas.prediction import ClassPrediction, ErrorResponse, PredictResponse
from backend.services.gradcam_service import GradCAMService
from backend.services.inference import InferenceService
from backend.services.preprocessing import decode_image

logger = get_logger(__name__)

router = APIRouter(tags=["prediction"])


@router.post(
    "/predict",
    response_model=PredictResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid, corrupt, empty, or oversized image."},
        500: {"model": ErrorResponse, "description": "Model or Grad-CAM inference failure."},
    },
    summary="Diagnose a crop disease from a leaf image",
    description=(
        "Accepts a single leaf image (multipart/form-data), runs it through the "
        "EfficientNet-B0 classifier, and returns the top prediction, a ranked "
        "top-K list, and a Grad-CAM heatmap explaining which regions of the leaf "
        "drove the prediction."
    ),
)
async def predict(
    image: UploadFile = File(..., description="Leaf image file (JPEG, PNG, etc.), max 10MB."),
    inference_service: InferenceService = Depends(get_inference_service),
    gradcam_service: GradCAMService = Depends(get_gradcam_service),
    settings: Settings = Depends(get_settings),
) -> PredictResponse:
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

    processing_time_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "predict: file=%s prediction=%s confidence=%.4f total_time_ms=%.1f",
        image.filename, result.class_name, result.confidence, processing_time_ms,
    )

    return PredictResponse(
        prediction=result.class_name,
        confidence=result.confidence,
        top_predictions=[
            ClassPrediction(class_name=score.class_name, confidence=score.confidence)
            for score in result.top_k
        ],
        heatmap=heatmap,
        processing_time_ms=processing_time_ms,
    )
