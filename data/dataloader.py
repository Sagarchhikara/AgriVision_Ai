"""
dataloader.py

Builds PyTorch DataLoaders for train/val/test splits, driven by config.yaml
(batch_size, num_workers, pin_memory) rather than hardcoded values, so the
same code scales from a laptop CPU run to a GPU training box without edits.

Design notes
------------
- shuffle=True only for train; val/test must stay in a fixed order for
  reproducible evaluation and for correctly matching predictions to
  filenames/labels later (e.g. for the confusion matrix and Grad-CAM examples).
- An optional WeightedRandomSampler is provided (off by default) to address
  the class imbalance noted in EDA (~150 to ~3200 images/class). It's kept
  as an opt-in so the first baseline stays simple; enable it in Stage 2 if
  minority classes (e.g. rare diseases) underperform in the classification report.
- drop_last=True on train avoids a final partial batch destabilizing
  BatchNorm statistics on small last batches.
"""

from typing import Optional
import torch
from torch.utils.data import DataLoader, WeightedRandomSampler

from data.dataset import CropDiseaseDataset


def _build_weighted_sampler(dataset: CropDiseaseDataset) -> WeightedRandomSampler:
    """
    Build a sampler that oversamples minority classes so each batch sees a
    more balanced mix of classes, without discarding any majority-class data.
    """
    targets = [label for _, label in dataset.samples]
    class_counts = torch.bincount(torch.tensor(targets))
    class_weights = 1.0 / class_counts.float()
    sample_weights = [class_weights[label] for label in targets]
    return WeightedRandomSampler(
        weights=sample_weights,
        num_samples=len(sample_weights),
        replacement=True,
    )


def build_dataloader(
    dataset: CropDiseaseDataset,
    split: str,
    batch_size: int = 32,
    num_workers: int = 4,
    pin_memory: bool = True,
    use_weighted_sampler: bool = False,
) -> DataLoader:
    """
    Build a DataLoader for a given split.

    Args:
        dataset: a CropDiseaseDataset instance (from dataset.build_dataset)
        split: one of "train", "val", "test" — controls shuffle/drop_last behavior
        batch_size: from config.yaml training.batch_size
        num_workers: parallel data-loading workers
        pin_memory: speeds up host->GPU transfer; keep True if training on GPU
        use_weighted_sampler: if True and split == "train", oversamples minority
            classes to counter class imbalance. Ignored for val/test.
    """
    split = split.lower()
    is_train = split == "train"

    sampler = None
    shuffle = is_train

    if is_train and use_weighted_sampler:
        sampler = _build_weighted_sampler(dataset)
        shuffle = False  # sampler and shuffle are mutually exclusive in DataLoader

    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        sampler=sampler,
        num_workers=num_workers,
        pin_memory=pin_memory,
        drop_last=is_train,
    )


def build_dataloaders_from_config(config: dict, root_dir: str):
    """
    Convenience function: builds train/val/test datasets + dataloaders in one
    call, driven entirely by a loaded config.yaml dict.

    Example:
        import yaml
        config = yaml.safe_load(open("configs/config.yaml"))
        loaders = build_dataloaders_from_config(config, config["dataset"]["root"])
        train_loader = loaders["train"]
    """
    from data.transforms import get_transforms
    from data.dataset import build_dataset

    image_size = config["training"]["image_size"]
    batch_size = config["training"]["batch_size"]
    num_workers = config.get("dataset", {}).get("num_workers", 4)
    pin_memory = config.get("dataset", {}).get("pin_memory", True)
    use_weighted_sampler = config.get("dataset", {}).get("use_weighted_sampler", False)

    loaders = {}
    for split in ("train", "val", "test"):
        transform = get_transforms(split, image_size=image_size)
        dataset = build_dataset(root_dir, split, transform=transform)
        loaders[split] = build_dataloader(
            dataset,
            split=split,
            batch_size=batch_size,
            num_workers=num_workers,
            pin_memory=pin_memory,
            use_weighted_sampler=use_weighted_sampler,
        )

    return loaders