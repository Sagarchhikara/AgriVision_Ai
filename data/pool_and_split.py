"""
data/pool_and_split.py

Pools shared classes between PlantVillage and PlantDoc datasets, performs perceptual hash
(phash) deduplication across the combined pool, and creates a dual-source stratified
70/15/15 train/val/test split.
"""

import argparse
import os
import shutil
from collections import defaultdict
from pathlib import Path

import imagehash
from PIL import Image
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent.parent
PLANTVILLAGE_DIR = BASE_DIR / "datasets" / "PlantVillage"
PLANTDOC_DIR = BASE_DIR / "datasets" / "PlantDoc"
OUTPUT_DIR = BASE_DIR / "datasets"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def find_files_by_source(dataset_dir: Path):
    """
    Finds all class subfolders and associated image filepaths under dataset_dir.
    Handles both direct class subfolders and split subfolders (train/val/test).
    Returns dict: {class_name: [list of image paths]}
    """
    class_to_files = defaultdict(list)
    if not dataset_dir.exists():
        return class_to_files

    subdirs = [d for d in dataset_dir.iterdir() if d.is_dir()]
    split_names = [d.name for d in subdirs if d.name in {"train", "val", "test"}]

    if split_names:
        for s in split_names:
            s_dir = dataset_dir / s
            for c in s_dir.iterdir():
                if c.is_dir() and c.name not in {"train", "val", "test"}:
                    for f in c.iterdir():
                        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS:
                            class_to_files[c.name].append(f)
    else:
        for c in subdirs:
            if c.is_dir() and c.name not in {"train", "val", "test"}:
                for f in c.iterdir():
                    if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS:
                        class_to_files[c.name].append(f)

    return class_to_files


def compute_phash_clusters(filepaths: list):
    """
    Computes perceptual hashes (phash) for a list of filepaths.
    Returns dict: {phash_str: [list of filepaths]}
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


def split_cluster_list(cluster_ids, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, seed=42):
    """Robustly splits a list of cluster IDs into train/val/test."""
    if not cluster_ids:
        return [], [], []
    n = len(cluster_ids)
    if n == 1:
        return cluster_ids, [], []
    if n == 2:
        return [cluster_ids[0]], [cluster_ids[1]], []
    if n == 3:
        return [cluster_ids[0], cluster_ids[1]], [cluster_ids[2]], []

    train_ids, rest_ids = train_test_split(
        cluster_ids, train_size=train_ratio, random_state=seed, shuffle=True
    )
    if len(rest_ids) <= 1:
        val_ids = rest_ids
        test_ids = []
    else:
        val_relative = val_ratio / (val_ratio + test_ratio)
        val_ids, test_ids = train_test_split(
            rest_ids, train_size=val_relative, random_state=seed, shuffle=True
        )
    return train_ids, val_ids, test_ids


def make_safe_filename(src_fpath: Path) -> str:
    src_path = Path(src_fpath)
    prefix = "pd_" if "PlantDoc" in str(src_path) else "pv_"
    name = src_path.name
    ext = src_path.suffix
    if len(name) > 100:
        stem = src_path.stem[:90]
        name = f"{stem}{ext}"
    return f"{prefix}{name}"


def pool_and_split(
    pv_dir: Path = PLANTVILLAGE_DIR,
    pd_dir: Path = PLANTDOC_DIR,
    output_dir: Path = OUTPUT_DIR,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
    clean: bool = True,
):
    print(f"Scanning PlantVillage directory: {pv_dir}")
    pv_class_map = find_files_by_source(pv_dir)

    print(f"Scanning PlantDoc directory: {pd_dir}")
    pd_class_map = find_files_by_source(pd_dir)

    pv_classes = set(c for c, files in pv_class_map.items() if len(files) > 0)
    pd_classes = set(c for c, files in pd_class_map.items() if len(files) > 0)

    shared_classes = sorted(list(pv_classes.intersection(pd_classes)))

    print(f"\nFound {len(pv_classes)} PlantVillage classes, {len(pd_classes)} PlantDoc classes.")
    print(f"Targeting {len(shared_classes)} SHARED classes for combined model pool.")

    if not shared_classes:
        print("Error: No shared classes found between PlantVillage and PlantDoc!")
        return

    # Optionally clean existing split subfolders (train, val, test) in output_dir
    if clean:
        for split_name in ["train", "val", "test"]:
            split_path = output_dir / split_name
            if split_path.exists():
                print(f"Cleaning existing split directory '{split_path}'...")
                shutil.rmtree(split_path)

    summary_rows = []
    total_pv_count = 0
    total_pd_count = 0
    total_pooled_count = 0
    total_train_count = 0
    total_val_count = 0
    total_test_count = 0

    print("\nProcessing deduplication & dual-source stratified splitting per class...")

    for cls in shared_classes:
        pv_files = pv_class_map[cls]
        pd_files = pd_class_map[cls]

        # 1. Deduplicate PlantVillage images via phash
        pv_hashes = compute_phash_clusters(pv_files)
        pv_cids = list(pv_hashes.keys())
        pv_tr_cids, pv_va_cids, pv_te_cids = split_cluster_list(pv_cids, train_ratio, val_ratio, test_ratio, seed)

        # 2. Deduplicate PlantDoc images via phash
        pd_hashes = compute_phash_clusters(pd_files)
        pd_cids = list(pd_hashes.keys())
        pd_tr_cids, pd_va_cids, pd_te_cids = split_cluster_list(pd_cids, train_ratio, val_ratio, test_ratio, seed)

        # Collect file lists for each split
        tr_files = [f for cid in pv_tr_cids for f in pv_hashes[cid]] + [f for cid in pd_tr_cids for f in pd_hashes[cid]]
        va_files = [f for cid in pv_va_cids for f in pv_hashes[cid]] + [f for cid in pd_va_cids for f in pd_hashes[cid]]
        te_files = [f for cid in pv_te_cids for f in pv_hashes[cid]] + [f for cid in pd_te_cids for f in pd_hashes[cid]]

        # Copy files to output splits
        for split_name, file_list in [("train", tr_files), ("val", va_files), ("test", te_files)]:
            dest_dir = output_dir / split_name / cls
            dest_dir.mkdir(parents=True, exist_ok=True)
            for src_fpath in file_list:
                dest_fname = make_safe_filename(src_fpath)
                shutil.copy2(src_fpath, dest_dir / dest_fname)


        pv_len = len(pv_files)
        pd_len = len(pd_files)
        pooled_len = pv_len + pd_len

        tr_len = len(tr_files)
        va_len = len(va_files)
        te_len = len(te_files)

        total_pv_count += pv_len
        total_pd_count += pd_len
        total_pooled_count += pooled_len
        total_train_count += tr_len
        total_val_count += va_len
        total_test_count += te_len

        summary_rows.append({
            "class": cls,
            "pv_count": pv_len,
            "pd_count": pd_len,
            "pooled": pooled_len,
            "train": tr_len,
            "val": va_len,
            "test": te_len,
        })

    print("\n" + "=" * 80)
    print("COMBINED DATASET POOLING & STRATIFIED SPLIT SUMMARY")
    print("=" * 80)
    print(f"{'Class Name':42s} | {'PV':6s} | {'PD':5s} | {'Total':6s} | {'Train':6s} | {'Val':5s} | {'Test':5s}")
    print("-" * 80)
    for r in summary_rows:
        print(f"{r['class']:42s} | {r['pv_count']:6d} | {r['pd_count']:5d} | {r['pooled']:6d} | {r['train']:6d} | {r['val']:5d} | {r['test']:5d}")
    print("=" * 80)
    print(f"{'TOTALS (' + str(len(shared_classes)) + ' Shared Classes)':42s} | {total_pv_count:6d} | {total_pd_count:5d} | {total_pooled_count:6d} | {total_train_count:6d} | {total_val_count:5d} | {total_test_count:5d}")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Pool and split PlantVillage + PlantDoc on shared classes.")
    parser.add_argument("--pv-dir", type=Path, default=PLANTVILLAGE_DIR, help="Path to PlantVillage directory")
    parser.add_argument("--pd-dir", type=Path, default=PLANTDOC_DIR, help="Path to PlantDoc directory")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR, help="Output root directory")
    parser.add_argument("--train", type=float, default=0.70, help="Train ratio (default: 0.70)")
    parser.add_argument("--val", type=float, default=0.15, help="Val ratio (default: 0.15)")
    parser.add_argument("--test", type=float, default=0.15, help="Test ratio (default: 0.15)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--clean", action="store_true", default=True, help="Clean existing output split directories")
    args = parser.parse_args()

    pool_and_split(
        pv_dir=args.pv_dir,
        pd_dir=args.pd_dir,
        output_dir=args.output,
        train_ratio=args.train,
        val_ratio=args.val,
        test_ratio=args.test,
        seed=args.seed,
        clean=args.clean,
    )


if __name__ == "__main__":
    main()
