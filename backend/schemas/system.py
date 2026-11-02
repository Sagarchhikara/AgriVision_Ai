"""
backend/schemas/system.py

Response models for the two service-status endpoints: GET / and GET /health.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.report import SupportedLanguage


class RootResponse(BaseModel):
    """Response body for GET /."""

    message: str  = Field(..., description="Static confirmation that the backend process is up.")

    model_config = ConfigDict(json_schema_extra={"example": {"message": "AgriVision_Ai backend running"}})


class HealthResponse(BaseModel):
    """Response body for GET /health, intended for uptime checks / load-balancer probes."""

    status: str = Field(..., description="'healthy' if the model is loaded and ready to serve requests.")
    model_loaded: bool = Field(..., description="Whether the checkpoint has been loaded into memory.")
    device: str = Field(..., description="Device inference currently runs on, e.g. 'cuda', 'mps', 'cpu'.")
    cuda_available: bool = Field(..., description="Whether torch.cuda.is_available() on this host.")
    version: str = Field(..., description="Backend application version.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "model_loaded": True,
                "device": "cuda",
                "cuda_available": True,
                "version": "0.1.0",
            }
        }
    )


class MetaResponse(BaseModel):
    """Response body for GET /meta: what a client needs to build its UI and validate input."""

    classes: list[str] = Field(
        ..., description="Every class the model can predict, in the model's output order."
    )
    languages: list[SupportedLanguage] = Field(..., description="Supported report languages.")
    default_language: str = Field(..., description="Language used when a request names none.")
    max_upload_bytes: int = Field(..., description="Largest accepted image upload, in bytes.")
    allowed_image_types: list[str] = Field(..., description="Accepted image upload content types.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "classes": ["Apple___Apple_scab", "Apple___Cedar_apple_rust", "Apple___healthy"],
                "languages": ["en", "hi", "pa"],
                "default_language": "en",
                "max_upload_bytes": 10485760,
                "allowed_image_types": ["image/jpeg", "image/png", "image/webp"],
            }
        }
    )
