"""
backend/services/gradcam_service.py

Grad-CAM heatmap generation, reusing the already-loaded model and the
already-computed prediction rather than doing either a second time.

Design notes
------------
- utils/gradcam.py's GradCAMExplainer is a standalone-script utility: it
  builds/loads its own model copy from a checkpoint path, opens images from
  disk, and uses a different (plain square-resize) preprocessing pipeline
  than the one evaluate.py used to report accuracy. None of that fits a
  request-serving path, so this service talks to pytorch_grad_cam directly
  -- same library calls (GradCAM, ClassifierOutputTarget, show_cam_on_image),
  just wired for in-memory reuse:
    * the model is the SAME loaded singleton from InferenceService -- no
      second checkpoint load, no second copy of the model in memory;
    * the target class is the prediction InferenceService already computed,
      so Grad-CAM's one forward+backward pass targets that class directly
      instead of re-discovering the top-1 class with a redundant forward pass;
    * the base image is ImagePreprocessor.to_display_array's output, pixel-
      aligned with the tensor the model actually saw.
- Grad-CAM needs gradients, unlike InferenceService.predict (which runs under
  torch.inference_mode(), incompatible with autograd) -- so this necessarily
  runs one fresh, grad-enabled forward+backward per request. That's the one
  unavoidable extra pass; generate_heatmap() runs it exactly once.
"""

from __future__ import annotations

import base64
import io

import numpy as np
import torch
from PIL import Image
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

from backend.core.logging import get_logger
from backend.services.inference import InferenceService
from backend.utils.exceptions import InferenceError

logger = get_logger(__name__)


class GradCAMService:
    """Generates a Grad-CAM overlay using the shared, already-loaded model."""

    def __init__(self, inference_service: InferenceService):
        self.inference_service = inference_service
        model = inference_service.model

        if not hasattr(model, "get_target_layer"):
            raise InferenceError("Model does not expose get_target_layer(); cannot run Grad-CAM.")
        self.target_layers = [model.get_target_layer()]
        logger.info("Grad-CAM service ready (target layer=%s)", type(self.target_layers[0]).__name__)

    def generate_heatmap(
        self,
        input_tensor: torch.Tensor,
        display_image: np.ndarray,
        target_class_idx: int,
    ) -> str:
        """
        Args:
            input_tensor: the SAME (1, 3, H, W) normalized tensor used for
                prediction (ImagePreprocessor.to_tensor output), created
                outside any torch.inference_mode() context.
            display_image: float32 (H, W, 3) array in [0, 1], pixel-aligned
                with input_tensor (ImagePreprocessor.to_display_array output).
            target_class_idx: the class to explain -- the prediction
                InferenceService.predict already produced, so Grad-CAM
                doesn't rediscover it with its own forward pass.

        Returns:
            A base64-encoded PNG data URI of the CAM overlay:
            "data:image/png;base64,...".

        Raises:
            InferenceError: if the CAM computation itself fails.
        """
        model = self.inference_service.model
        device = self.inference_service.device
        tensor = input_tensor.to(device)

        targets = [ClassifierOutputTarget(target_class_idx)]

        try:
            with GradCAM(model=model, target_layers=self.target_layers) as cam:
                grayscale_cam = cam(input_tensor=tensor, targets=targets)[0, :]
        except Exception as exc:
            raise InferenceError(f"Grad-CAM generation failed: {exc}") from exc

        cam_image = show_cam_on_image(display_image, grayscale_cam, use_rgb=True)
        return self._encode_png_base64(cam_image)

    @staticmethod
    def _encode_png_base64(rgb_uint8: np.ndarray) -> str:
        buffer = io.BytesIO()
        Image.fromarray(rgb_uint8).save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/png;base64,{encoded}"
