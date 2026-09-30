"""
backend/utils/exceptions.py

Typed exception hierarchy for the backend.

Each service raises the most specific subclass of AgriVisionError that
applies. A single exception handler in the API layer catches AgriVisionError
and maps `error_code` + `status_code` + the message to an ErrorResponse,
so no endpoint needs its own try/except boilerplate for these cases.
"""

from __future__ import annotations


class AgriVisionError(Exception):
    """Base class for backend errors that map to a specific HTTP response."""

    error_code: str = "internal_error"
    status_code: int = 500


class ImageValidationError(AgriVisionError):
    """Raised for empty, oversized, corrupt, or unsupported-format uploads."""

    error_code = "invalid_image"
    status_code = 400


class InferenceError(AgriVisionError):
    """Raised when the model/Grad-CAM pipeline fails on an otherwise-valid image."""

    error_code = "inference_error"


class ReportError(AgriVisionError):
    """Base for every failure in the LLM report layer."""

    error_code = "report_error"


class ReportDisabledError(ReportError):
    """Raised when a report is requested but the LLM layer is turned off in config."""

    error_code = "report_disabled"
    status_code = 503


class LLMConfigurationError(ReportError):
    """Raised at startup for an unusable provider setup, e.g. a missing API key."""

    error_code = "llm_configuration_error"


class LLMProviderError(ReportError):
    """Raised when the upstream LLM API returns an error or unreadable response."""

    error_code = "llm_provider_error"
    status_code = 502


class LLMTimeoutError(ReportError):
    """Raised when the upstream LLM API does not respond within the configured timeout."""

    error_code = "llm_timeout"
    status_code = 504


class LLMRateLimitError(ReportError):
    """Raised when the upstream LLM API rejects the call with a rate limit (429)."""

    error_code = "llm_rate_limited"
    status_code = 429


class ReportParseError(ReportError):
    """Raised when the LLM's output still isn't schema-valid JSON after one retry."""

    error_code = "report_parse_error"
    status_code = 502
