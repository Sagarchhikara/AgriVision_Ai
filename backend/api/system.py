"""
backend/api/system.py

Service-status endpoints: GET / (liveness) and GET /health (readiness, with
model/device/version info) -- used for uptime checks and load-balancer probes --
plus GET /meta, the static facts a client needs to build its UI.
"""

from __future__ import annotations

from typing import get_args

import torch
from fastapi import APIRouter, Depends, Request

from backend.api.deps import get_inference_service
from backend.core.config import Settings, get_settings
from backend.schemas.report import SupportedLanguage
from backend.schemas.system import HealthResponse, MetaResponse, RootResponse
from backend.services.inference import InferenceService
from backend.services.preprocessing import ALLOWED_IMAGE_TYPES

router = APIRouter(tags=["system"])


@router.get(
    "/",
    response_model=RootResponse,
    summary="Liveness check",
    description="Confirms the backend process is up. Does not check model readiness -- see /health for that.",
)
async def root() -> RootResponse:
    return RootResponse(message="AgriVision_Ai backend running")


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Readiness check",
    description="Reports whether the model is loaded, which device it's running on, and CUDA availability.",
)
async def health(request: Request, settings: Settings = Depends(get_settings)) -> HealthResponse:
    inference_service = getattr(request.app.state, "inference_service", None)
    model_loaded = inference_service is not None
    device = str(inference_service.device) if model_loaded else settings.device

    return HealthResponse(
        status="healthy" if model_loaded else "unhealthy",
        model_loaded=model_loaded,
        device=device,
        cuda_available=torch.cuda.is_available(),
        version=settings.app_version,
    )


@router.get(
    "/meta",
    response_model=MetaResponse,
    summary="Client metadata",
    description=(
        "The model's class list, supported report languages, and upload limits, so a "
        "client can build its UI and validate input without hardcoding any of them."
    ),
)
async def meta(
    inference_service: InferenceService = Depends(get_inference_service),
    settings: Settings = Depends(get_settings),
) -> MetaResponse:
    return MetaResponse(
        classes=inference_service.class_names,
        languages=list(get_args(SupportedLanguage)),
        default_language=settings.llm_default_language,
        max_upload_bytes=settings.max_upload_bytes,
        allowed_image_types=list(ALLOWED_IMAGE_TYPES),
    )
