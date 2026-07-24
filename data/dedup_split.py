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
4. Stratify by class so class proportions are preserved across splits, same
   as the original 70/15/15 script.

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


def compute_hashes(class_dir: str) -> dict:
    """
    Returns {phash_str: [list of image filenames with that hash]} for one class folder.
    Near-duplicate images (small rotations/crops) tend to collapse to the same
    or a very close phash; here we use exact phash string match, which is the
    conservative choice for grouping obvious duplicates. hash_size=8 (default)
    is a reasonable balance of sensitivity vs over-grouping distinct images.
    """
    hash_to_files = defaultdict(list)
    for fname in os.listdir(class_dir):
        fpath = os.path.join(class_dir, fname)
        try:
            with Image.open(fpath) as img:
                h = str(imagehash.phash(img))
            hash_to_files[h].append(fname)
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


def copy_files(class_dir, filenames, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    for fname in filenames:
        shutil.copy2(os.path.join(class_dir, fname), os.path.join(dest_dir, fname))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="Path to PlantVillage/ (class subfolders)")
    parser.add_argument("--output", required=True, help="Output root, will create train/val/test under it")
    parser.add_argument("--train", type=float, default=0.70)
    parser.add_argument("--val", type=float, default=0.15)
    parser.add_argument("--test", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    assert abs(args.train + args.val + args.test - 1.0) < 1e-6, "Ratios must sum to 1.0"

    class_names = sorted(
        d for d in os.listdir(args.source) if os.path.isdir(os.path.join(args.source, d))
    )

    total_clusters = 0
    total_images = 0
    duplicate_clusters = 0

    for class_name in class_names:
        class_dir = os.path.join(args.source, class_name)
        print(f"Hashing {class_name}...")
        hash_to_files = compute_hashes(class_dir)

        cluster_ids = list(hash_to_files.keys())
        n_images = sum(len(v) for v in hash_to_files.values())
        n_dupe_clusters = sum(1 for v in hash_to_files.values() if len(v) > 1)

        total_clusters += len(cluster_ids)
        total_images += n_images
        duplicate_clusters += n_dupe_clusters

        print(f"  {n_images} images -> {len(cluster_ids)} unique-leaf clusters "
              f"({n_dupe_clusters} clusters have duplicates)")

        train_ids, val_ids, test_ids = split_clusters(
            cluster_ids, args.train, args.val, args.test, args.seed
        )

        for split_name, ids in [("train", train_ids), ("val", val_ids), ("test", test_ids)]:
            files = [f for cid in ids for f in hash_to_files[cid]]
            dest = os.path.join(args.output, split_name, class_name)
            copy_files(class_dir, files, dest)
            print(f"    {split_name}: {len(files)} images from {len(ids)} clusters")

    print(f"\nDone. {total_images} images, {total_clusters} unique-leaf clusters, "
          f"{duplicate_clusters} clusters contained duplicates/near-duplicates.")
    print("If duplicate_clusters is a large fraction of total_clusters, that confirms "
          "the original random split was very likely leaking near-duplicates across splits.")


if __name__ == "__main__":
    main()
