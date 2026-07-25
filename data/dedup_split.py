"""
data/dedup_split.py

Re-splits the PlantVillage dataset into train/val/test while preventing
near-duplicate leaf images from leaking across splits.

Why this exists
----------------
PlantVillage contains many near-identical images per physical leaf (captured
under slightly different rotation/crop/lighting during data collection). A
naive random file-level split (train_test_split on individual filenames) will
scatter these near-duplicates across train and val/test. The model then gets
val "unseen" images that are near-copies of training images, inflating
accuracy far above what it would achieve on genuinely new field photos.

Approach
--------
1. Compute a perceptual hash (phash) for every image. Near-duplicate images
   produce identical or near-identical hashes even with small transformations.
2. Group images by hash into clusters (a cluster = one physical leaf's set of
   near-duplicate captures).
3. Split at the CLUSTER level, not the file level, per class — so every
   duplicate of a given leaf ends up entirely in train, entirely in val, or
   entirely in test, never split across them.
4. Stratify by class so class proportions are preserved across splits (70/15/15).

Usage:
    python data/dedup_split.py --source datasets/PlantVillage --output datasets/ \
        --train 0.70 --val 0.15 --test 0.15
"""

import argparse
import os
import shutil
from collections import defaultdict

import imagehash
from PIL import Image
from sklearn.model_selection import train_test_split


def find_classes_and_files(source_dir: str):
    """
    Finds all class names and associated image filepaths under source_dir.
    Handles both direct class subfolders (e.g. source_dir/Apple___Black_rot/)
    and nested split subfolders (e.g. source_dir/train/Apple___Black_rot/).
    """
    subdirs = [d for d in os.listdir(source_dir) if os.path.isdir(os.path.join(source_dir, d))]
    split_names = [d for d in subdirs if d in {"train", "val", "test"}]

    class_to_filepaths = defaultdict(list)
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}

    if split_names:
        for s in split_names:
            s_dir = os.path.join(source_dir, s)
            for c in os.listdir(s_dir):
                c_dir = os.path.join(s_dir, c)
                if os.path.isdir(c_dir):
                    for fname in os.listdir(c_dir):
                        ext = os.path.splitext(fname)[1].lower()
                        if ext in IMAGE_EXTENSIONS:
                            class_to_filepaths[c].append(os.path.join(c_dir, fname))
    else:
        for c in subdirs:
            c_dir = os.path.join(source_dir, c)
            for fname in os.listdir(c_dir):
                ext = os.path.splitext(fname)[1].lower()
                if ext in IMAGE_EXTENSIONS:
                    class_to_filepaths[c].append(os.path.join(c_dir, fname))

    return class_to_filepaths


def compute_hashes(filepaths: list) -> dict:
    """
    Returns {phash_str: [list of image filepaths with that hash]} for a class.
    Near-duplicate images (small rotations/crops) tend to collapse to the same
    or a very close phash; exact phash string match is the conservative choice
    for grouping obvious duplicates.
    """
    hash_to_files = defaultdict(list)
    for fpath in filepaths:
        try:
            with Image.open(fpath) as img:
                h = str(imagehash.phash(img))
            hash_to_files[h].append(fpath)
        except Exception as e:
            print(f"  Skipping unreadable file {fpath}: {e}")
    return hash_to_files


def split_clusters(cluster_ids, train_ratio, val_ratio, test_ratio, seed):
    """Splits a list of cluster ids into train/val/test at the cluster level."""
    train_ids, rest_ids = train_test_split(
        cluster_ids, train_size=train_ratio, random_state=seed
    )
    val_relative = val_ratio / (val_ratio + test_ratio)
    val_ids, test_ids = train_test_split(
        rest_ids, train_size=val_relative, random_state=seed
    )
    return train_ids, val_ids, test_ids


def copy_files(filepaths, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    for fpath in filepaths:
        fname = os.path.basename(fpath)
        shutil.copy2(fpath, os.path.join(dest_dir, fname))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="Path to PlantVillage/ (class subfolders or split subfolders)")
    parser.add_argument("--output", required=True, help="Output root, will create train/val/test under it")
    parser.add_argument("--train", type=float, default=0.70)
    parser.add_argument("--val", type=float, default=0.15)
    parser.add_argument("--test", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--clean", action="store_true", help="Clean existing output split subfolders first")
    args = parser.parse_args()

    assert abs(args.train + args.val + args.test - 1.0) < 1e-6, "Ratios must sum to 1.0"

    print(f"Scanning '{args.source}' for class image files...")
    class_to_filepaths = find_classes_and_files(args.source)
    class_names = sorted(class_to_filepaths.keys())

    if not class_names:
        print(f"Error: No class directories or image files found in '{args.source}'")
        return

    print(f"Found {len(class_names)} classes across '{args.source}'")
    print(f"Splitting ratios -> Train: {args.train:.0%}, Val: {args.val:.0%}, Test: {args.test:.0%}")
    print(f"Output directory -> '{args.output}'\n")

    # Optionally clean existing split folders in output dir
    if args.clean:
        for split_name in ["train", "val", "test"]:
            split_dir = os.path.join(args.output, split_name)
            if os.path.exists(split_dir):
                print(f"Cleaning existing output split directory '{split_dir}'...")
                shutil.rmtree(split_dir)

    total_clusters = 0
    total_images = 0
    duplicate_clusters = 0
    split_counts = defaultdict(lambda: defaultdict(int))

    for class_name in class_names:
        filepaths = class_to_filepaths[class_name]
        print(f"Hashing {class_name} ({len(filepaths)} images)...")
        hash_to_files = compute_hashes(filepaths)

        cluster_ids = list(hash_to_files.keys())
        n_images = sum(len(v) for v in hash_to_files.values())
        n_dupe_clusters = sum(1 for v in hash_to_files.values() if len(v) > 1)

        total_clusters += len(cluster_ids)
        total_images += n_images
        duplicate_clusters += n_dupe_clusters

        print(f"  {n_images} images -> {len(cluster_ids)} unique-leaf clusters "
              f"({n_dupe_clusters} clusters have near-duplicates)")

        train_ids, val_ids, test_ids = split_clusters(
            cluster_ids, args.train, args.val, args.test, args.seed
        )

        for split_name, ids in [("train", train_ids), ("val", val_ids), ("test", test_ids)]:
            files = [f for cid in ids for f in hash_to_files[cid]]
            dest = os.path.join(args.output, split_name, class_name)
            copy_files(files, dest)
            split_counts[split_name][class_name] = len(files)
            print(f"    {split_name}: {len(files)} images from {len(ids)} clusters")

    print(f"\n" + "=" * 60)
    print(f"Deduplicated split completed successfully!")
    print(f"Total processed images: {total_images}")
    print(f"Total unique-leaf clusters: {total_clusters}")
    print(f"Duplicate clusters: {duplicate_clusters}")
    train_total = sum(split_counts["train"].values())
    val_total = sum(split_counts["val"].values())
    test_total = sum(split_counts["test"].values())
    print(f"Summary -> Train: {train_total} | Val: {val_total} | Test: {test_total}")
    print("=" * 60)

    # Sanity-check per-class split sizes
    print("\n--- Per-Class Split Size Sanity Check ---")
    thin_splits = []
    for cls in class_names:
        tr = split_counts["train"][cls]
        va = split_counts["val"][cls]
        te = split_counts["test"][cls]
        tot = tr + va + te
        print(f"{cls:45s} | Total: {tot:5d} | Train: {tr:5d} | Val: {va:4d} | Test: {te:4d}")
        if va < 15 or te < 15:
            thin_splits.append((cls, va, te))

    if thin_splits:
        print("\n[WARNING] Small class split alert:")
        for cls, va, te in thin_splits:
            print(f"  Class '{cls}' has small partitions -> Val: {va}, Test: {te}")
    else:
        print("\nAll classes have sufficient samples in train, val, and test partitions.")


if __name__ == "__main__":
    main()
