"""
utils/eda_generator.py

Automated EDA Generator for AgriVision AI.
Analyzes PlantVillage, PlantDoc, and Combined datasets, generating figures
and statistical metrics for reporting and notebook integration.
"""

import os
import sys
import json
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image

# Set random seed for reproducibility
np.random.seed(42)

# Set base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATASETS_DIR = BASE_DIR / "datasets"
PLANTVILLAGE_DIR = DATASETS_DIR / "PlantVillage"
PLANTDOC_DIR = DATASETS_DIR / "PlantDoc"
OUTPUT_FIG_DIR = BASE_DIR / "outputs" / "eda_figures"
OUTPUT_FIG_DIR.mkdir(parents=True, exist_ok=True)

# Styling
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams.update({
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'figure.titlesize': 16,
    'font.family': 'sans-serif'
})


def collect_dataset_stats(dataset_path: Path, is_split_format: bool = False):
    """
    Traverses dataset directory, collecting image paths, classes, dimensions,
    file sizes, modes, and formats.
    """
    class_counts = defaultdict(int)
    image_records = []
    corrupted_files = []
    
    if not dataset_path.exists():
        print(f"Warning: Directory {dataset_path} does not exist!")
        return None

    # Supported image extensions
    valid_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}

    for root, dirs, files in os.walk(dataset_path):
        for f in files:
            ext = Path(f).suffix.lower()
            if ext in valid_exts:
                fpath = Path(root) / f
                rel = fpath.relative_to(dataset_path)
                parts = rel.parts
                
                # Determine split and class name
                split_name = "all"
                if len(parts) >= 2 and parts[0] in ["train", "val", "test"]:
                    split_name = parts[0]
                    cls_name = parts[1]
                elif len(parts) >= 2:
                    cls_name = parts[0]
                else:
                    cls_name = "unknown"
                    
                class_counts[cls_name] += 1
                stat = fpath.stat()
                
                # Quick inspection of PIL image header
                try:
                    with Image.open(fpath) as img:
                        w, h = img.size
                        mode = img.mode
                        fmt = img.format or ext[1:].upper()
                        image_records.append({
                            'filepath': str(fpath),
                            'filename': f,
                            'class': cls_name,
                            'split': split_name,
                            'width': w,
                            'height': h,
                            'aspect_ratio': round(w / h, 3),
                            'mode': mode,
                            'format': fmt,
                            'size_kb': round(stat.st_size / 1024, 2)
                        })
                except Exception as e:
                    corrupted_files.append((str(fpath), str(e)))

    df = pd.DataFrame(image_records)
    return {
        'df': df,
        'class_counts': dict(sorted(class_counts.items(), key=lambda x: x[1], reverse=True)),
        'corrupted': corrupted_files,
        'total_images': len(df),
        'num_classes': len(class_counts)
    }


def plot_class_distribution(class_counts: dict, title: str, filename: str, color='#2b5c8f', top_n=None):
    """Plots clean bar chart of class distributions."""
    items = list(class_counts.items())
    if top_n and len(items) > top_n:
        items = items[:top_n]
    
    classes = [k for k, v in items]
    counts = [v for k, v in items]
    
    fig, ax = plt.subplots(figsize=(14, max(8, len(classes) * 0.35)))
    bars = ax.barh(classes[::-1], counts[::-1], color=color, edgecolor='none', alpha=0.85)
    
    # Add labels
    max_c = max(counts) if counts else 1
    for bar in bars:
        w = bar.get_width()
        ax.text(w + max_c * 0.01, bar.get_y() + bar.get_height()/2, f"{int(w):,}",
                va='center', ha='left', fontsize=9, color='#333333', fontweight='bold')
        
    ax.set_title(title, pad=15, fontweight='bold')
    ax.set_xlabel('Number of Images')
    ax.set_ylabel('Class Label')
    ax.grid(axis='x', linestyle='--', alpha=0.5)
    plt.tight_layout()
    
    out_path = OUTPUT_FIG_DIR / filename
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved figure: {out_path}")


def plot_source_ratio_breakdown(pv_counts: dict, pd_counts: dict, filename: str):
    """Plots stacked bar chart showing PV vs PD image proportion in shared 28 classes."""
    shared_classes = sorted(list(set(pv_counts.keys()).intersection(set(pd_counts.keys()))))
    
    pv_vals = [pv_counts.get(c, 0) for c in shared_classes]
    pd_vals = [pd_counts.get(c, 0) for c in shared_classes]
    totals = [p + d for p, d in zip(pv_vals, pd_vals)]
    
    # Sort by total count
    sorted_indices = np.argsort(totals)[::-1]
    shared_classes = [shared_classes[i] for i in sorted_indices]
    pv_vals = [pv_vals[i] for i in sorted_indices]
    pd_vals = [pd_vals[i] for i in sorted_indices]
    totals = [totals[i] for i in sorted_indices]
    
    fig, ax = plt.subplots(figsize=(14, 10))
    y_pos = np.arange(len(shared_classes))
    
    ax.barh(y_pos, pv_vals, label='PlantVillage (Lab)', color='#2b5c8f', alpha=0.85)
    ax.barh(y_pos, pd_vals, left=pv_vals, label='PlantDoc (Field)', color='#e06d53', alpha=0.85)
    
    for i, (tot, pd_c) in enumerate(zip(totals, pd_vals)):
        pct_pd = (pd_c / tot * 100) if tot > 0 else 0
        ax.text(tot + 50, i, f"{tot:,} (PD: {pct_pd:.1f}%)", va='center', fontsize=8, color='#444444')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(shared_classes)
    ax.invert_yaxis()
    ax.set_xlabel('Total Image Count')
    ax.set_title('Shared 28 Classes: Composition of PlantVillage (Lab) vs PlantDoc (Field)', fontweight='bold', pad=15)
    ax.legend(loc='lower right', frameon=True)
    ax.grid(axis='x', linestyle='--', alpha=0.5)
    plt.tight_layout()
    
    out_path = OUTPUT_FIG_DIR / filename
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved figure: {out_path}")


def plot_resolution_and_aspect(df_pv: pd.DataFrame, df_pd: pd.DataFrame, filename: str):
    """Plots comparison of resolution and aspect ratios between datasets."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Image Width vs Height scatter / box plots
    data = []
    if df_pv is not None and not df_pv.empty:
        for _, row in df_pv.sample(min(1000, len(df_pv)), random_state=42).iterrows():
            data.append({'Dataset': 'PlantVillage', 'Width': row['width'], 'Height': row['height'], 'Aspect Ratio': row['aspect_ratio'], 'Size (KB)': row['size_kb']})
    if df_pd is not None and not df_pd.empty:
        for _, row in df_pd.sample(min(1000, len(df_pd)), random_state=42).iterrows():
            data.append({'Dataset': 'PlantDoc', 'Width': row['width'], 'Height': row['height'], 'Aspect Ratio': row['aspect_ratio'], 'Size (KB)': row['size_kb']})
            
    df_comp = pd.DataFrame(data)
    
    # 1. File Size comparison
    sns.boxplot(data=df_comp, x='Dataset', y='Size (KB)', ax=axes[0], palette=['#2b5c8f', '#e06d53'])
    axes[0].set_title('File Size Distribution (KB)', fontweight='bold')
    axes[0].set_ylabel('File Size (KB)')
    
    # 2. Aspect Ratio distribution
    sns.kdeplot(data=df_comp, x='Aspect Ratio', hue='Dataset', ax=axes[1], fill=True, palette=['#2b5c8f', '#e06d53'], common_norm=False)
    axes[1].set_title('Aspect Ratio Distribution (W / H)', fontweight='bold')
    axes[1].set_xlabel('Aspect Ratio')
    
    plt.tight_layout()
    out_path = OUTPUT_FIG_DIR / filename
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved figure: {out_path}")


def plot_split_distribution(combined_dir: Path, filename: str):
    """Plots train/val/test split breakdown for the pooled 28 classes."""
    splits = ['train', 'val', 'test']
    split_counts = defaultdict(lambda: defaultdict(int))
    
    for s in splits:
        s_dir = combined_dir / s
        if not s_dir.exists():
            continue
        for c in s_dir.iterdir():
            if c.is_dir():
                n_imgs = len([f for f in c.iterdir() if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']])
                split_counts[c.name][s] = n_imgs
                
    classes = sorted(split_counts.keys())
    train_counts = [split_counts[c]['train'] for c in classes]
    val_counts = [split_counts[c]['val'] for c in classes]
    test_counts = [split_counts[c]['test'] for c in classes]
    
    fig, ax = plt.subplots(figsize=(14, 10))
    y_pos = np.arange(len(classes))
    
    ax.barh(y_pos, train_counts, label='Train (70%)', color='#2b5c8f', alpha=0.85)
    ax.barh(y_pos, val_counts, left=train_counts, label='Val (15%)', color='#4ba375', alpha=0.85)
    
    left_test = np.array(train_counts) + np.array(val_counts)
    ax.barh(y_pos, test_counts, left=left_test, label='Test (15%)', color='#e06d53', alpha=0.85)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(classes)
    ax.invert_yaxis()
    ax.set_xlabel('Number of Images')
    ax.set_title('Stratified Dual-Source Train / Val / Test Split Breakdown (28 Pooled Classes)', fontweight='bold', pad=15)
    ax.legend(loc='lower right')
    ax.grid(axis='x', linestyle='--', alpha=0.5)
    plt.tight_layout()
    
    out_path = OUTPUT_FIG_DIR / filename
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved figure: {out_path}")


def generate_sample_comparison_grid(pv_dir: Path, pd_dir: Path, filename: str):
    """Generates visual sample grid comparing PlantVillage (lab) vs PlantDoc (field)."""
    # Sample 4 representative shared classes
    sample_classes = [
        "Apple___healthy",
        "Corn_(maize)___Common_rust_",
        "Potato___Early_blight",
        "Tomato___Late_blight"
    ]
    
    fig, axes = plt.subplots(len(sample_classes), 2, figsize=(8, 12))
    
    for i, cname in enumerate(sample_classes):
        # Find PV image
        pv_img_path = None
        for root, _, files in os.walk(pv_dir):
            if Path(root).name == cname:
                for f in files:
                    if Path(f).suffix.lower() in ['.jpg', '.jpeg', '.png']:
                        pv_img_path = Path(root) / f
                        break
            if pv_img_path:
                break
                
        # Find PD image
        pd_img_path = None
        for root, _, files in os.walk(pd_dir):
            if Path(root).name == cname:
                for f in files:
                    if Path(f).suffix.lower() in ['.jpg', '.jpeg', '.png']:
                        pd_img_path = Path(root) / f
                        break
            if pd_img_path:
                break
                
        # Plot PV
        if pv_img_path and pv_img_path.exists():
            img_pv = Image.open(pv_img_path)
            axes[i, 0].imshow(img_pv)
            axes[i, 0].set_title(f"PlantVillage (Lab): {cname.split('___')[0]}\n{cname.split('___')[1]}", fontsize=9)
        else:
            axes[i, 0].text(0.5, 0.5, "Image Not Found", ha='center', va='center')
        axes[i, 0].axis('off')
        
        # Plot PD
        if pd_img_path and pd_img_path.exists():
            img_pd = Image.open(pd_img_path)
            axes[i, 1].imshow(img_pd)
            axes[i, 1].set_title(f"PlantDoc (Field): {cname.split('___')[0]}\n{cname.split('___')[1]}", fontsize=9)
        else:
            axes[i, 1].text(0.5, 0.5, "Image Not Found", ha='center', va='center')
        axes[i, 1].axis('off')
        
    plt.tight_layout()
    out_path = OUTPUT_FIG_DIR / filename
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved figure: {out_path}")


def run_full_eda():
    """Main execution function."""
    print("=== Processing PlantVillage Dataset ===")
    pv_res = collect_dataset_stats(PLANTVILLAGE_DIR)
    
    print("\n=== Processing PlantDoc Dataset ===")
    pd_res = collect_dataset_stats(PLANTDOC_DIR)
    
    print("\n=== Processing Combined Dataset ===")
    comb_res = collect_dataset_stats(DATASETS_DIR, is_split_format=True)
    
    # 1. Plot individual distributions
    if pv_res:
        plot_class_distribution(pv_res['class_counts'], 
                              f"PlantVillage Class Distribution ({pv_res['total_images']:,} Images, {pv_res['num_classes']} Classes)", 
                              "pv_class_distribution.png", color='#2b5c8f')
        
    if pd_res:
        plot_class_distribution(pd_res['class_counts'], 
                              f"PlantDoc Class Distribution ({pd_res['total_images']:,} Images, {pd_res['num_classes']} Classes)", 
                              "pd_class_distribution.png", color='#e06d53')
        
    # 2. Source Ratio Breakdown
    if pv_res and pd_res:
        plot_source_ratio_breakdown(pv_res['class_counts'], pd_res['class_counts'], "source_ratio_breakdown.png")
        plot_resolution_and_aspect(pv_res['df'], pd_res['df'], "resolution_comparison.png")
        generate_sample_comparison_grid(PLANTVILLAGE_DIR, PLANTDOC_DIR, "sample_comparison_grid.png")
        
    # 3. Split Distribution
    plot_split_distribution(DATASETS_DIR, "split_distribution.png")
    
    # Output summary json
    summary_data = {
        'plantvillage': {
            'total_images': pv_res['total_images'] if pv_res else 0,
            'num_classes': pv_res['num_classes'] if pv_res else 0,
            'corrupted_files': len(pv_res['corrupted']) if pv_res else 0
        },
        'plantdoc': {
            'total_images': pd_res['total_images'] if pd_res else 0,
            'num_classes': pd_res['num_classes'] if pd_res else 0,
            'corrupted_files': len(pd_res['corrupted']) if pd_res else 0
        }
    }
    
    with open(OUTPUT_FIG_DIR / "summary_metrics.json", "w") as f:
        json.dump(summary_data, f, indent=2)
        
    print("\nEDA processing and figure generation complete!")

if __name__ == "__main__":
    run_full_eda()
