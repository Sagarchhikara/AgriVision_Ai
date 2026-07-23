"""
dataset.py

Wraps torchvision's ImageFolder to build train/val/test datasets from the
pre-split directory structure (datasets/train, datasets/val, datasets/test),
each containing one subfolder per class (e.g. Tomato___Late_blight/).

Design notes
------------
- ImageFolder is used instead of a custom Dataset because the directory layout
  already matches its expected structure exactly, and it gives us `.classes`
  and `.class_to_idx` for free — needed later for:
    * mapping model output indices back to human-readable disease names
      (for the LLM report generation stage)
    * labeling Grad-CAM heatmaps
- A thin wrapper class (CropDiseaseDataset) is kept around ImageFolder rather
  than using it directly, so we have one place to add dataset-level logic later
  (e.g. returning image paths alongside tensors for debugging, or filtering
  corrupt files) without touching the training loop.
"""

import os
from typing import Optional, Callable

from torchvision.datasets import ImageFolder


class CropDiseaseDataset(ImageFolder):
    """
    Thin wrapper around ImageFolder for a single split (train/val/test).

    Args:
        root: path to the split directory, e.g. "datasets/train"
        transform: torchvision transform pipeline (from transforms.py)
    """

    def __init__(self, root: str, transform: Optional[Callable] = None):
        if not os.path.isdir(root):
            raise FileNotFoundError(
                f"Dataset split directory not found: {root}. "
                f"Did you run the dataset split script first?"
            )
        super().__init__(root=root, transform=transform)

    @property
    def num_classes(self) -> int:
        return len(self.classes)

    def get_class_name(self, idx: int) -> str:
        """Map a predicted class index back to its human-readable folder name."""
        return self.classes[idx]


def build_dataset(root_dir: str, split: str, transform: Optional[Callable] = None) -> CropDiseaseDataset:
    """
    Build a CropDiseaseDataset for a given split.

    Args:
        root_dir: dataset root containing train/val/test subfolders, e.g. "datasets/"
        split: one of "train", "val", "test"
        transform: transform pipeline to apply (typically from transforms.get_transforms)
    """
    split_dir = os.path.join(root_dir, split)
    return CropDiseaseDataset(root=split_dir, transform=transform)