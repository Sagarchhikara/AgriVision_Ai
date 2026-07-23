"""
transforms.py

Defines image transformation pipelines for training, validation, and test sets.

Design notes
------------
- Train transforms include augmentation to improve generalization, which matters
  more here because the dataset has real class imbalance (smallest class ~150
  images vs largest ~3200).
- Val/Test transforms are deterministic (resize + center crop + normalize only) so
  that evaluation numbers are stable and comparable across runs/checkpoints.
- ImageNet mean/std are used because EfficientNet-B0 is pretrained on ImageNet;
  matching normalization statistics is required for transfer learning to work well.
"""

from torchvision import transforms

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def get_train_transforms(image_size: int = 224) -> transforms.Compose:
    """
    Training transforms: augmentation + normalization.

    RandomResizedCrop (rather than plain Resize) forces the model to learn
    disease features at different scales/crops of the leaf, which helps since
    leaf disease lesions can appear anywhere in the frame and at varying sizes.
    """
    return transforms.Compose([
        transforms.RandomResizedCrop(image_size, scale=(0.8, 1.0)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.2),  # leaves have no fixed "up", unlike e.g. faces
        transforms.RandomRotation(degrees=20),
        transforms.ColorJitter(
            brightness=0.2,
            contrast=0.2,
            saturation=0.2,
            hue=0.05,
        ),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])


def get_val_transforms(image_size: int = 224) -> transforms.Compose:
    """
    Validation/Test transforms: deterministic resize + center crop, no augmentation.

    A slightly larger resize before center-cropping (standard ImageNet practice)
    avoids cutting off the edges of the leaf in a single resize step.
    """
    resize_size = int(image_size * 1.14)  # e.g. 224 -> ~256, matches ImageNet convention
    return transforms.Compose([
        transforms.Resize(resize_size),
        transforms.CenterCrop(image_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])


def get_transforms(split: str, image_size: int = 224) -> transforms.Compose:
    """
    Convenience dispatcher so callers don't need to import both functions.

    Args:
        split: one of "train", "val", "test"
        image_size: target square image size (matches config.yaml training.image_size)
    """
    split = split.lower()
    if split == "train":
        return get_train_transforms(image_size)
    elif split in ("val", "test"):
        return get_val_transforms(image_size)
    else:
        raise ValueError(f"Unknown split '{split}'. Expected 'train', 'val', or 'test'.")