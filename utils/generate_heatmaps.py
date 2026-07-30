"""
utils/generate_heatmaps.py

Script to generate, analyze, and save Grad-CAM heatmaps for both correctly
classified and misclassified test set images.

Saves curated artifacts to:
  - outputs/heatmaps/correct/
  - outputs/heatmaps/misclassified/
  - outputs/heatmaps/curated/
"""

import os
import yaml
import torch
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from tqdm import tqdm

from data.dataset import build_dataset
from utils.gradcam import load_model_for_gradcam, GradCAMExplainer


def save_side_by_side(rgb_img, cam_img, true_label, pred_label, conf, status, save_path):
    """
    Saves a 3-panel figure: Original Image | Heatmap Overlay | Pure Heatmap / Comparison.
    """
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.5))

    # Original RGB
    axes[0].imshow(rgb_img)
    axes[0].set_title("Original Image", fontsize=11, fontweight="bold")
    axes[0].axis("off")

    # Grad-CAM Overlay
    axes[1].imshow(cam_img)
    axes[1].set_title("Grad-CAM Heatmap Overlay", fontsize=11, fontweight="bold")
    axes[1].axis("off")

    # Blend comparison / Difference
    axes[2].imshow(cam_img)
    color = "green" if status == "CORRECT" else "red"
    title_text = f"Status: {status}\nTrue: {true_label}\nPred: {pred_label} ({conf:.2%})"
    axes[2].set_title(title_text, fontsize=10, color=color, fontweight="bold")
    axes[2].axis("off")

    plt.suptitle(f"XAI Grad-CAM Analysis — {status}", fontsize=13, fontweight="bold", y=0.98)
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=200, bbox_inches="tight")
    plt.close()


def generate_all_heatmaps(dataset_root=None, misclassified_csv=None, output_dir=None):
    config_path = "configs/config.yaml"
    checkpoint_path = "outputs/checkpoints/best.pt"

    config = yaml.safe_load(open(config_path))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device for Grad-CAM generation: {device}")

    dataset_root = dataset_root or config["dataset"]["root"]

    if not output_dir:
        if "PlantDoc" in str(dataset_root):
            output_dir = "outputs/heatmaps_plantdoc"
        else:
            output_dir = "outputs/heatmaps"

    if not misclassified_csv:
        if "PlantDoc" in str(dataset_root):
            misclassified_csv = "outputs/predictions_plantdoc/misclassified.csv"
        else:
            misclassified_csv = "outputs/predictions/misclassified.csv"

    os.makedirs(os.path.join(output_dir, "correct"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "misclassified"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "curated"), exist_ok=True)

    print(f"Generating heatmaps for dataset root: {dataset_root}")
    print(f"Saving outputs to: {output_dir}")

    # Build dataset to get class list & samples
    test_dataset = build_dataset(dataset_root, "test")
    class_names = test_dataset.classes
    class_to_idx = {name: idx for idx, name in enumerate(class_names)}
    print(f"Loaded dataset with {len(class_names)} classes.")


    # Load model & explainer
    model = load_model_for_gradcam(checkpoint_path, config, len(class_names), device)
    explainer = GradCAMExplainer(model, device=device)

    # 1. Load misclassified info
    mis_df = pd.read_csv(misclassified_csv) if os.path.exists(misclassified_csv) else pd.DataFrame()
    misclassified_paths = set(mis_df["filepath"].values) if len(mis_df) > 0 else set()

    print(f"Found {len(misclassified_paths)} misclassified samples in {misclassified_csv}")

    # 2. Sample Correctly Classified Images
    # Target diverse classes (1.00 F1 score classes + healthy vs diseased)
    target_classes = [
        "Apple___Apple_scab",
        "Apple___Black_rot",
        "Apple___healthy",
        "Corn_(maize)___Common_rust_",
        "Corn_(maize)___healthy",
        "Grape___Black_rot",
        "Grape___Esca_(Black_Measles)",
        "Orange___Haunglongbing_(Citrus_greening)",
        "Potato___Early_blight",
        "Squash___Powdery_mildew",
        "Tomato___Bacterial_spot",
        "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
        "Tomato___healthy",
    ]

    correct_samples = []
    samples_per_class = 2

    # Organize test dataset samples by class
    class_samples_map = {cls_name: [] for cls_name in class_names}
    for path, label_idx in test_dataset.samples:
        if path not in misclassified_paths:
            class_samples_map[class_names[label_idx]].append(path)

    print("\n--- Generating Grad-CAM for Correctly Classified Images ---")
    correct_counter = 0
    for cls_name in target_classes:
        if cls_name not in class_samples_map:
            continue
        available_paths = class_samples_map[cls_name]
        selected_paths = available_paths[:samples_per_class]

        for idx, img_path in enumerate(selected_paths):
            true_label = cls_name
            res = explainer.explain(img_path)
            pred_label = class_names[res["pred_class_idx"]]

            # Verify it is indeed correctly classified
            if pred_label == true_label:
                sanitized_cls = cls_name.replace("/", "_")
                filename = f"correct_{sanitized_cls}_sample{idx+1}.png"

                # Save 3-panel side-by-side visualization
                side_save_path = os.path.join(output_dir, "correct", filename)
                save_side_by_side(
                    res["rgb_image"], res["cam_image"],
                    true_label, pred_label, res["confidence"],
                    "CORRECT", side_save_path
                )

                # Save standalone CAM image for frontend / curated use
                curated_cam_path = os.path.join(output_dir, "curated", f"cam_{sanitized_cls}_sample{idx+1}.png")
                Image.fromarray(res["cam_image"]).save(curated_cam_path)

                correct_counter += 1

    print(f"Saved {correct_counter} correctly classified heatmap visualizations.")

    # 3. Sample Misclassified Images
    print("\n--- Generating Grad-CAM for Misclassified Images ---")
    mis_counter = 0
    if len(mis_df) > 0:
        for idx, row in mis_df.iterrows():
            img_path = row["filepath"]
            true_label = row["true_label"]
            pred_label = row["predicted_label"]
            conf = row["confidence"]

            if not os.path.exists(img_path):
                continue

            true_idx = class_to_idx.get(true_label, None)
            pred_idx = class_to_idx.get(pred_label, None)

            # Explain for top predicted class (why model made this mistake)
            res_pred = explainer.explain(img_path, target_category=pred_idx)

            sanitized_true = true_label.replace("/", "_")
            sanitized_pred = pred_label.replace("/", "_")
            filename = f"misclassified_err{idx+1}_{sanitized_true}_vs_{sanitized_pred}.png"

            side_save_path = os.path.join(output_dir, "misclassified", filename)
            save_side_by_side(
                res_pred["rgb_image"], res_pred["cam_image"],
                true_label, pred_label, conf,
                "MISCLASSIFIED", side_save_path
            )

            # Also save to curated directory
            curated_cam_path = os.path.join(output_dir, "curated", f"cam_error_{idx+1}.png")
            Image.fromarray(res_pred["cam_image"]).save(curated_cam_path)

            mis_counter += 1

    print(f"Saved {mis_counter} misclassified heatmap visualizations.")
    print(f"\nAll Grad-CAM outputs successfully saved under {output_dir}/")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset_root", default=None, help="Dataset root dir (e.g. datasets/ or datasets/PlantDoc)")
    parser.add_argument("--misclassified_csv", default=None, help="Path to misclassified.csv")
    parser.add_argument("--output_dir", default=None, help="Output directory for heatmaps")
    args = parser.parse_args()

    generate_all_heatmaps(
        dataset_root=args.dataset_root,
        misclassified_csv=args.misclassified_csv,
        output_dir=args.output_dir,
    )

