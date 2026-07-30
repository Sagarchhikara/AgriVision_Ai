"""
backend/api/system.py

Service-status endpoints: GET / (liveness) and GET /health (readiness, with
model/device/version info) -- used for uptime checks and load-balancer probes.
"""

from __future__ import annotations

import torch
from fastapi import APIRouter, Depends, Request

from backend.core.config import Settings, get_settings
from backend.schemas.system import HealthResponse, RootResponse

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
