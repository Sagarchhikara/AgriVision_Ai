"""
backend/services/preprocessing.py

Turns raw uploaded bytes into a model-ready tensor and a display-ready RGB
array, shared by both the inference service and the Grad-CAM service.

Design notes
------------
- `decode_image` validates before any PIL/torch call touches the bytes, so a
  corrupt/empty/non-image upload fails fast with a specific, catchable
  ImageValidationError instead of surfacing as an opaque stack trace deep in
  decoding.
- `ImagePreprocessor` reuses data.transforms.get_val_transforms rather than
  hand-rolling a duplicate pipeline, so the backend applies EXACTLY the
  preprocessing evaluate.py used to report ~96% test accuracy (resize short
  side to ~1.14x image_size -> center crop -> ImageNet normalize). Any
  divergence here would silently change inference-time behavior relative to
  what was actually benchmarked offline.
- The Grad-CAM display array is produced by reapplying the same Resize/
  CenterCrop transform *objects* (not a re-derived formula), so it is
  pixel-aligned with what the model actually saw and can't drift if the
  resize ratio in get_val_transforms ever changes.
"""

from __future__ import annotations

import io

import numpy as np
import torch
from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from data.transforms import get_val_transforms
from backend.core.logging import get_logger
from backend.utils.exceptions import (
    ImageTooLargeError,
    ImageValidationError,
    UnsupportedImageTypeError,
)

logger = get_logger(__name__)

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

# Accepted upload content types, mapped to the Pillow format the decoded bytes
# must actually turn out to be. The header alone is client-controlled, so a
# BMP or TIFF sent as image/jpeg is still rejected once decoded.
ALLOWED_IMAGE_TYPES: dict[str, str] = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}

_READ_CHUNK_BYTES = 64 * 1024


def _too_large_message(max_size_bytes: int) -> str:
    return f"Uploaded file exceeds the {max_size_bytes // (1024 * 1024)}MB limit."


async def read_upload(upload: UploadFile, max_size_bytes: int = MAX_UPLOAD_SIZE_BYTES) -> bytes:
    """
    Check the declared content type, then read the upload in chunks, stopping
    as soon as it passes the size limit rather than buffering all of it first.

    Raises:
        UnsupportedImageTypeError: content type is not in ALLOWED_IMAGE_TYPES.
        ImageTooLargeError: the upload is larger than max_size_bytes.
    """
    if upload.content_type not in ALLOWED_IMAGE_TYPES:
        raise UnsupportedImageTypeError(
            f"Unsupported file type '{upload.content_type}'. "
            f"Accepted types: {', '.join(ALLOWED_IMAGE_TYPES)}."
        )

    chunks: list[bytes] = []
    total = 0
    while chunk := await upload.read(_READ_CHUNK_BYTES):
        total += len(chunk)
        if total > max_size_bytes:
            raise ImageTooLargeError(_too_large_message(max_size_bytes))
        chunks.append(chunk)
    return b"".join(chunks)


def decode_image(file_bytes: bytes, max_size_bytes: int = MAX_UPLOAD_SIZE_BYTES) -> Image.Image:
    """
    Validate and decode raw upload bytes into a PIL RGB image.

    Args:
        file_bytes: raw contents of the uploaded file.
        max_size_bytes: rejects uploads larger than this (default 10MB).

    Raises:
        ImageValidationError: empty upload, or bytes that don't decode as an image.
        ImageTooLargeError: oversized upload.
        UnsupportedImageTypeError: decodes, but not as one of ALLOWED_IMAGE_TYPES.
    """
    if not file_bytes:
        raise ImageValidationError("Uploaded file is empty.")
    if len(file_bytes) > max_size_bytes:
        raise ImageTooLargeError(_too_large_message(max_size_bytes))

    try:
        # verify() is a cheap structural check; Pillow requires the file to be
        # reopened afterwards since verify() leaves the parser in a used state.
        Image.open(io.BytesIO(file_bytes)).verify()
        opened = Image.open(io.BytesIO(file_bytes))
        image_format = opened.format
        image = opened.convert("RGB")
    except (UnidentifiedImageError, SyntaxError, ValueError, OSError) as exc:
        raise ImageValidationError("Uploaded file is not a valid image (failed to decode).") from exc

    if image_format not in ALLOWED_IMAGE_TYPES.values():
        raise UnsupportedImageTypeError(
            f"Unsupported image format '{image_format}'. Accepted types: {', '.join(ALLOWED_IMAGE_TYPES)}."
        )

    return image


class ImagePreprocessor:
    """
    Wraps the eval-time transform pipeline for repeated use across requests.

    Instantiate once (per image_size) and reuse — building the torchvision
    transform pipeline is not free, and there's no reason to redo it per request.
    """

    def __init__(self, image_size: int = 224):
        self.image_size = image_size
        self._tensor_transform = get_val_transforms(image_size)
        # get_val_transforms is Resize -> CenterCrop -> ToTensor -> Normalize;
        # reusing the first two ops keeps the display image pixel-aligned with
        # the model input without duplicating the resize-ratio arithmetic.
        self._resize_op, self._crop_op = self._tensor_transform.transforms[:2]

    def to_tensor(self, image: Image.Image) -> torch.Tensor:
        """Returns a normalized (1, 3, H, W) batch tensor ready for the model."""
        return self._tensor_transform(image).unsqueeze(0)

    def to_display_array(self, image: Image.Image) -> np.ndarray:
        """
        Returns a float32 (H, W, 3) array in [0, 1], resized+center-cropped to
        the same region the model sees — used as the Grad-CAM base image.
        """
        cropped = self._crop_op(self._resize_op(image))
        return np.asarray(cropped, dtype=np.float32) / 255.0
