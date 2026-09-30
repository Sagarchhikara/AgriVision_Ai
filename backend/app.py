"""
backend/app.py

FastAPI application factory: wires settings, logging, the model-loading
services, CORS, exception handling, and routes together.

The model is loaded exactly once here, inside `lifespan`, before the app
starts accepting requests -- never inside a route handler, never lazily on
first request.

Run with:
    uvicorn backend.app:app --host 0.0.0.0 --port 8000
or:
    python -m backend.app
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api import predict as predict_routes
from backend.api import report as report_routes
from backend.api import system as system_routes
from backend.core.config import get_settings
from backend.core.logging import get_logger, setup_logging
from backend.schemas.prediction import ErrorResponse
from backend.services.gradcam_service import GradCAMService
from backend.services.inference import InferenceService
from backend.services.llm import build_provider
from backend.services.report_cache import build_cache
from backend.services.report_service import ReportService
from backend.utils.exceptions import AgriVisionError, ImageValidationError

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Loads the model once at startup and tears down cleanly at shutdown."""
    settings = get_settings()

    logger.info("Starting %s v%s", settings.app_name, settings.app_version)
    start = time.perf_counter()

    inference_service = InferenceService(settings)
    gradcam_service = GradCAMService(inference_service)

    # One AsyncClient for the process, like the model: connection pooling is the
    # whole point, and a per-request client would throw the pool away each time.
    # build_provider raises here if a real provider is selected without an API
    # key, so a misconfigured deployment fails at startup, not mid-request.
    llm_client = httpx.AsyncClient()
    report_service = ReportService(
        settings=settings,
        provider=build_provider(settings, llm_client),
        cache=build_cache(
            enabled=settings.llm_cache_enabled,
            ttl_seconds=settings.llm_cache_ttl_seconds,
            max_entries=settings.llm_cache_max_entries,
        ),
    )

    app.state.settings = settings
    app.state.inference_service = inference_service
    app.state.gradcam_service = gradcam_service
    app.state.report_service = report_service

    logger.info("Startup complete in %.1fms", (time.perf_counter() - start) * 1000)
    yield

    await llm_client.aclose()
    logger.info("Shutting down %s", settings.app_name)


def _register_exception_handlers(app: FastAPI) -> None:
    """
    Maps the backend's typed exceptions to a uniform ErrorResponse body.

    Registration order doesn't matter here -- Starlette resolves the handler
    by walking the exception's MRO for the most specific registered type, so
    ImageValidationError (a client error) and its AgriVisionError base
    (server error) resolve independently even though one subclasses the other.
    """

    @app.exception_handler(ImageValidationError)
    async def handle_image_validation_error(request: Request, exc: ImageValidationError) -> JSONResponse:
        logger.warning("Invalid image upload: %s", exc)
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(error=exc.error_code, detail=str(exc)).model_dump(),
        )

    @app.exception_handler(AgriVisionError)
    async def handle_agrivision_error(request: Request, exc: AgriVisionError) -> JSONResponse:
        logger.error("Backend error [%s]: %s", exc.error_code, exc, exc_info=True)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(error=exc.error_code, detail=str(exc)).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning("Request validation failed: %s", exc)
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(error="validation_error", detail=str(exc)).model_dump(),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="internal_error", detail="An unexpected error occurred."
            ).model_dump(),
        )


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level, settings.log_file)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Inference backend for AgriVision_Ai: EfficientNet-B0 crop disease "
            "classification with Grad-CAM explainability."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _register_exception_handlers(app)

    app.include_router(system_routes.router)
    app.include_router(predict_routes.router)
    app.include_router(report_routes.router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run("backend.app:app", host=settings.host, port=settings.port, reload=False)
