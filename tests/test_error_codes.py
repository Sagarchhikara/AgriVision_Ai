"""
tests/test_error_codes.py

ErrorResponse.error is a closed literal, so an exception whose error_code is
missing from it would fail validation inside the error handler itself. This
keeps the literal and the exception hierarchy in sync.
"""

from __future__ import annotations

from typing import get_args

from backend.schemas.prediction import ErrorCode
from backend.utils import exceptions


def _all_subclasses(cls: type) -> set[type]:
    direct = set(cls.__subclasses__())
    return direct.union(*(_all_subclasses(sub) for sub in direct))


def test_every_exception_error_code_is_a_declared_error_code():
    error_codes = {
        cls.error_code for cls in _all_subclasses(exceptions.AgriVisionError) | {exceptions.AgriVisionError}
    }

    assert error_codes <= set(get_args(ErrorCode))


def test_status_codes_for_upload_errors():
    assert exceptions.ImageValidationError.status_code == 400
    assert exceptions.ImageTooLargeError.status_code == 413
    assert exceptions.UnsupportedImageTypeError.status_code == 415
