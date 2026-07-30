"""
backend/utils/exceptions.py

Typed exception hierarchy for the backend.

Each service raises the most specific subclass of AgriVisionError that
applies. A single exception handler in the API layer catches AgriVisionError
and maps `error_code` + the message to an ErrorResponse and HTTP status,
so no endpoint needs its own try/except boilerplate for these cases.
"""

from __future__ import annotations


class AgriVisionError(Exception):
    """Base class for backend errors that map to a specific HTTP response."""

    error_code: str = "internal_error"


class ImageValidationError(AgriVisionError):
    """Raised for empty, oversized, corrupt, or unsupported-format uploads."""

    error_code = "invalid_image"


class InferenceError(AgriVisionError):
    """Raised when the model/Grad-CAM pipeline fails on an otherwise-valid image."""

    error_code = "inference_error"
