import argparse
from pathlib import Path
import random
import shutil
import sys

# Base project directory (2 levels up from data/split_dataset.py)
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE_DIR = BASE_DIR / "datasets" / "PlantVillage"
DEFAULT_OUTPUT_DIR = BASE_DIR / "datasets"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def split_dataset(
    source_dir: Path = DEFAULT_SOURCE_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
    clean_existing: bool = False,
):
    """Splits a class-subfolder dataset into train, val, and test splits."""
    random.seed(seed)

    source_dir = Path(source_dir).resolve()
    output_dir = Path(output_dir).resolve()

    if not source_dir.exists():
        print(f"Error: Source directory '{source_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if not source_dir.is_dir():
        print(f"Error: Source path '{source_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    # Validate ratios
    total_ratio = train_ratio + val_ratio + test_ratio
    if not abs(total_ratio - 1.0) < 1e-5:
        print(
            f"Error: Ratios must sum to 1.0 (got train={train_ratio}, val={val_ratio}, test={test_ratio}, sum={total_ratio}).",
            file=sys.stderr,
        )
        sys.exit(1)

    classes = [
        folder
        for folder in source_dir.iterdir()
        if folder.is_dir() and folder.name not in {"train", "val", "test"}
    ]

    if not classes:
        print(f"Error: No class directories found in '{source_dir}'.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(classes)} classes in '{source_dir}'")
    print(f"Splitting ratios -> Train: {train_ratio:.0%}, Val: {val_ratio:.0%}, Test: {test_ratio:.0%}")
    print(f"Target directory -> '{output_dir}'\n")

    # Optionally clean existing split directories
    if clean_existing:
        for split_name in ["train", "val", "test"]:
            split_path = output_dir / split_name
            if split_path.exists():
                print(f"Cleaning existing split directory '{split_path}'...")
                shutil.rmtree(split_path)

    total_images_processed = 0
    split_counts = {"train": 0, "val": 0, "test": 0}

    for cls in sorted(classes, key=lambda c: c.name):
        images = [
            f
            for f in cls.glob("*")
            if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
        ]

        random.shuffle(images)
        total = len(images)

        if total == 0:
            print(f"Warning: No valid images found in class folder '{cls.name}'. Skipping.")
            continue

        train_end = int(total * train_ratio)
        val_end = train_end + int(total * val_ratio)

        splits = {
            "train": images[:train_end],
            "val": images[train_end:val_end],
            "test": images[val_end:],
        }

        for split_name, split_images in splits.items():
            destination = output_dir / split_name / cls.name
            destination.mkdir(parents=True, exist_ok=True)

            for image in split_images:
                shutil.copy2(image, destination / image.name)

            split_counts[split_name] += len(split_images)

        total_images_processed += total
        print(
            f"Class '{cls.name}': {total} images -> "
            f"train: {len(splits['train'])}, val: {len(splits['val'])}, test: {len(splits['test'])}"
        )

    print("\n" + "=" * 50)
    print("Dataset split completed successfully!")
    print(f"Total processed images: {total_images_processed}")
    print(
        f"Summary -> Train: {split_counts['train']} | Val: {split_counts['val']} | Test: {split_counts['test']}"
    )
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="Split dataset into train, val, and test sets.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE_DIR, help="Path to source dataset directory")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR, help="Path to output dataset directory")
    parser.add_argument("--train-ratio", type=float, default=0.7, help="Train ratio (default: 0.7)")
    parser.add_argument("--val-ratio", type=float, default=0.15, help="Val ratio (default: 0.15)")
    parser.add_argument("--test-ratio", type=float, default=0.15, help="Test ratio (default: 0.15)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for shuffling (default: 42)")
    parser.add_argument("--clean", action="store_true", help="Clean output split directories before splitting")

    args = parser.parse_args()

    split_dataset(
        source_dir=args.source,
        output_dir=args.output,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed,
        clean_existing=args.clean,
    )


if __name__ == "__main__":
    main()