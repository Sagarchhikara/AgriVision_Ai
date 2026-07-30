"""
utils/generate_field_heatmaps.py

Generates and saves Grad-CAM heatmaps specifically for cluttered, field-condition
PlantDoc images (prefixed with `pd_`) evaluated on the fine-tuned 28-class model.

Saves 3-panel visualization artifacts to:
  - outputs/heatmaps_field_plantdoc/correct/
  - outputs/heatmaps_field_plantdoc/misclassified/
  - outputs/heatmaps_field_plantdoc/curated/
"""

import os
import yaml
import torch
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path
from collections import defaultdict


from data.dataset import build_dataset
from utils.gradcam import load_model_for_gradcam, GradCAMExplainer


def save_side_by_side(rgb_img, cam_img, true_label, pred_label, conf, status, save_path):
    """
    Saves a 3-panel figure: Original Field Image | Grad-CAM Heatmap Overlay | Prediction Status.
    """
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.5))

    # Original RGB
    axes[0].imshow(rgb_img)
    axes[0].set_title("Original Field Image (PlantDoc)", fontsize=11, fontweight="bold")
    axes[0].axis("off")

    # Grad-CAM Overlay
    axes[1].imshow(cam_img)
    axes[1].set_title("Fine-Tuned Grad-CAM Heatmap", fontsize=11, fontweight="bold")
    axes[1].axis("off")

    # Status and confidence
    axes[2].imshow(cam_img)
    color = "#1b5e20" if status == "CORRECT" else "#b71c1c"
    title_text = f"Status: {status}\nTrue: {true_label}\nPred: {pred_label} ({conf:.2%})"
    axes[2].set_title(title_text, fontsize=10, color=color, fontweight="bold")
    axes[2].axis("off")

    plt.suptitle(f"Field Robustness XAI (PlantDoc Cluttered Background) — {status}", fontsize=13, fontweight="bold", y=0.98)
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=200, bbox_inches="tight")
    plt.close()


def main():
    config_path = "configs/config.yaml"
    checkpoint_path = "outputs/checkpoints/best.pt"
    misclassified_csv = "outputs/predictions/misclassified.csv"
    output_dir = "outputs/heatmaps_field_plantdoc"

    os.makedirs(os.path.join(output_dir, "correct"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "misclassified"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "curated"), exist_ok=True)

    config = yaml.safe_load(open(config_path))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device for Field Heatmap generation: {device}")

    # Build test dataset
    test_dataset = build_dataset("datasets", "test")
    class_names = test_dataset.classes
    class_to_idx = {name: idx for idx, name in enumerate(class_names)}
    print(f"Loaded combined test dataset with {len(class_names)} classes.")

    # Load fine-tuned model & explainer
    model = load_model_for_gradcam(checkpoint_path, config, len(class_names), device)
    explainer = GradCAMExplainer(model, device=device)

    # Load misclassified info
    mis_df = pd.read_csv(misclassified_csv) if os.path.exists(misclassified_csv) else pd.DataFrame()
    misclassified_paths = set(mis_df["filepath"].values) if len(mis_df) > 0 else set()

    # Filter test dataset samples specifically for PlantDoc images (pd_ prefix)
    pd_test_samples = [
        (path, label_idx) for path, label_idx in test_dataset.samples
        if os.path.basename(path).startswith("pd_")
    ]
    print(f"Found {len(pd_test_samples)} PlantDoc field-condition images in test split.")

    # Group PlantDoc test samples into correct vs misclassified
    pd_correct_map = defaultdict(list)
    pd_misclassified_rows = []

    for path, label_idx in pd_test_samples:
        if path in misclassified_paths:
            # find row in mis_df
            matching_rows = mis_df[mis_df["filepath"] == path]
            if len(matching_rows) > 0:
                pd_misclassified_rows.append(matching_rows.iloc[0])
        else:
            pd_correct_map[class_names[label_idx]].append(path)

    # 1. Process Correctly Classified PlantDoc Field Images
    print("\n--- Generating Heatmaps for Correctly Classified Field Images ---")
    correct_count = 0
    for cls_name, paths in pd_correct_map.items():
        # Pick up to 2 images per class
        for idx, img_path in enumerate(paths[:2]):
            res = explainer.explain(img_path)
            pred_label = class_names[res["pred_class_idx"]]

            if pred_label == cls_name:
                sanitized_cls = cls_name.replace("/", "_")
                filename = f"field_correct_{sanitized_cls}_{idx+1}.png"

                save_path = os.path.join(output_dir, "correct", filename)
                save_side_by_side(
                    res["rgb_image"], res["cam_image"],
                    cls_name, pred_label, res["confidence"],
                    "CORRECT", save_path
                )

                curated_path = os.path.join(output_dir, "curated", f"cam_field_{sanitized_cls}_{idx+1}.png")
                Image.fromarray(res["cam_image"]).save(curated_path)
                correct_count += 1

    print(f"Saved {correct_count} correct field heatmap visualizations.")

    # 2. Process Misclassified PlantDoc Field Images
    print("\n--- Generating Heatmaps for Misclassified Field Images ---")
    mis_count = 0
    for idx, row in enumerate(pd_misclassified_rows):
        img_path = row["filepath"]
        true_label = row["true_label"]
        pred_label = row["predicted_label"]
        conf = row["confidence"]

        if not os.path.exists(img_path):
            continue

        pred_idx = class_to_idx.get(pred_label, None)
        res = explainer.explain(img_path, target_category=pred_idx)

        sanitized_true = true_label.replace("/", "_")
        sanitized_pred = pred_label.replace("/", "_")
        filename = f"field_misclassified_{idx+1}_{sanitized_true}_vs_{sanitized_pred}.png"

        save_path = os.path.join(output_dir, "misclassified", filename)
        save_side_by_side(
            res["rgb_image"], res["cam_image"],
            true_label, pred_label, conf,
            "MISCLASSIFIED", save_path
        )

        curated_path = os.path.join(output_dir, "curated", f"cam_field_error_{idx+1}.png")
        Image.fromarray(res["cam_image"]).save(curated_path)
        mis_count += 1

    print(f"Saved {mis_count} misclassified field heatmap visualizations.")
    print(f"\nAll field Grad-CAM heatmaps successfully saved to {output_dir}/")


if __name__ == "__main__":
    main()
