"""
backend/schemas/system.py

Response models for the two service-status endpoints: GET / and GET /health.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


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
