"""
backend/services/inference.py

Model-loading singleton and prediction service.

Design notes
------------
- The checkpoint (outputs/checkpoints/best.pt) stores only model/optimizer
  state + epoch/best_acc -- no class names. Class names are re-derived here
  via torchvision.datasets.folder.find_classes on datasets/<split>, the exact
  discovery step ImageFolder used during training, so the index->name mapping
  can never drift from what the model was actually trained on.
- Built with pretrained=False even though config.yaml's `model.pretrained` is
  true -- that flag only matters for *training* (ImageNet-initialized
  backbone before fine-tuning). At serving time the checkpoint's state_dict
  fully overwrites the backbone anyway, so downloading ImageNet weights here
  would just be a slower, network-dependent no-op.
- predict() uses torch.inference_mode() (stricter/faster than no_grad) since
  this path never needs autograd. Grad-CAM generation is a separate service
  that runs its own gradient-enabled forward+backward on demand, so each kind
  of forward pass happens exactly once per request.
- InferenceService is intentionally NOT a lazily-cached singleton -- construct
  one explicitly during app startup and reuse it for the process lifetime, so
  "load the model only once" is enforced by the caller's lifecycle rather than
  an implicit cache that could be bypassed.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import torch
import torch.nn.functional as F
from torchvision.datasets.folder import find_classes

from backend.core.config import Settings
from backend.core.logging import get_logger
from backend.services.preprocessing import ImagePreprocessor
from backend.utils.exceptions import InferenceError
from models.model import CropDiseaseModel, build_model

logger = get_logger(__name__)


def resolve_device(device_setting: str) -> torch.device:
    """
    Resolve 'auto'/'cuda'/'mps'/'cpu' into a concrete, available torch.device.

    'auto' prefers CUDA, then Apple MPS, then falls back to CPU, so the same
    backend runs unmodified on a training GPU box, a dev Mac, or a bare CPU host.
    """
    if device_setting != "auto":
        return torch.device(device_setting)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def load_class_names(dataset_root: Path, split: str) -> list[str]:
    """
    Derive the model's output class ordering from datasets/<split>'s
    subdirectory listing -- the same discovery step ImageFolder performs
    internally, without scanning every image file.
    """
    split_dir = dataset_root / split
    if not split_dir.is_dir():
        raise InferenceError(f"Cannot derive class names: split directory not found at {split_dir}")
    classes, _ = find_classes(str(split_dir))
    if not classes:
        raise InferenceError(f"No class subdirectories found under {split_dir}")
    return classes


@dataclass
class ClassScore:
    class_name: str
    confidence: float


@dataclass
class PredictionResult:
    pred_class_idx: int
    class_name: str
    confidence: float
    top_k: list[ClassScore]
    input_tensor: torch.Tensor  # kept so Grad-CAM can reuse it without re-preprocessing
    inference_time_ms: float


class InferenceService:
    """Loads the trained model once and serves predictions for the process lifetime."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.device = resolve_device(settings.device)
        self.class_names = load_class_names(settings.dataset_root, settings.class_names_split)
        self.preprocessor = ImagePreprocessor(settings.image_size)

        logger.info(
            "Loading model '%s' (%d classes) on device=%s from checkpoint=%s",
            settings.model_name, len(self.class_names), self.device, settings.checkpoint_path,
        )
        self.model = self._load_model()
        logger.info("Model loaded and ready.")

    def _load_model(self) -> CropDiseaseModel:
        if not self.settings.checkpoint_path.is_file():
            raise InferenceError(f"Checkpoint not found at {self.settings.checkpoint_path}")

        model_config = {"model": {"name": self.settings.model_name, "pretrained": False}}
        model = build_model(model_config, num_classes=len(self.class_names))

        checkpoint = torch.load(self.settings.checkpoint_path, map_location=self.device)
        try:
            model.load_state_dict(checkpoint["model_state_dict"])
        except KeyError as exc:
            raise InferenceError(
                f"Checkpoint at {self.settings.checkpoint_path} is missing 'model_state_dict'"
            ) from exc

        model.to(self.device)
        model.eval()

        epoch, best_acc = checkpoint.get("epoch"), checkpoint.get("best_acc")
        if epoch is not None and best_acc is not None:
            logger.info("Checkpoint epoch=%s best_val_acc=%.4f", epoch, best_acc)

        return model

    @torch.inference_mode()
    def predict(self, input_tensor: torch.Tensor) -> PredictionResult:
        """
        Run a single forward pass and return the top-1 prediction plus a
        top-k ranked list.

        Args:
            input_tensor: a (1, 3, H, W) normalized batch tensor, as produced
                by ImagePreprocessor.to_tensor. Not re-preprocessed here, so
                the caller can hand the same tensor to the Grad-CAM service.
        """
        start = time.perf_counter()

        tensor = input_tensor.to(self.device)
        logits = self.model(tensor)
        probs = F.softmax(logits, dim=1).squeeze(0)

        k = min(self.settings.top_k, len(self.class_names))
        top_confidences, top_indices = probs.topk(k)

        top_k = [
            ClassScore(class_name=self.class_names[idx.item()], confidence=conf.item())
            for conf, idx in zip(top_confidences, top_indices)
        ]

        inference_time_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "Predicted '%s' (confidence=%.4f) in %.1fms",
            top_k[0].class_name, top_k[0].confidence, inference_time_ms,
        )

        return PredictionResult(
            pred_class_idx=top_indices[0].item(),
            class_name=top_k[0].class_name,
            confidence=top_k[0].confidence,
            top_k=top_k,
            input_tensor=input_tensor,
            inference_time_ms=inference_time_ms,
        )
