"""
backend/api/deps.py

FastAPI dependency accessors for services attached to app.state during
startup (backend/app.py's lifespan). Routes depend on these functions rather
than importing service singletons directly, so a route's dependencies are
declared in its signature and swappable in tests without touching route code.
"""

from __future__ import annotations

from fastapi import Request

from backend.services.gradcam_service import GradCAMService
from backend.services.inference import InferenceService
from backend.services.report_service import ReportService


def get_inference_service(request: Request) -> InferenceService:
    return request.app.state.inference_service


def get_gradcam_service(request: Request) -> GradCAMService:
    return request.app.state.gradcam_service


def get_report_service(request: Request) -> ReportService:
    return request.app.state.report_service
