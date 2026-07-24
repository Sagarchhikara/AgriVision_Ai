"""
evaluate.py

Standalone evaluation script. Loads the best checkpoint and runs inference
on the TEST split (never touched during training or checkpoint selection),
producing:
  - Full classification report (per-class precision/recall/F1/support)
  - Confusion matrix (saved as a heatmap PNG)
  - A CSV of misclassified examples (filepath, true label, predicted label,
    confidence) for manual/Grad-CAM inspection

Why test, not val
------------------
val accuracy is used to pick `best.pt` during training, so it's technically
"used" by the pipeline even though the model never trains on it directly.
Test is the only truly untouched number — this is the one to report and to
trust when judging whether accuracy is real or a leakage artifact.

Usage:
    python evaluate.py --checkpoint outputs/checkpoints/best.pt
"""

import argparse
import os

import yaml
import torch
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

from data.transforms import get_transforms
from data.dataset import build_dataset
from data.dataloader import build_dataloader
from models.model import build_model


def load_checkpoint(model, checkpoint_path, device):
    ckpt = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(ckpt["model_state_dict"])
    print(f"Loaded checkpoint from epoch {ckpt['epoch']} (best_acc={ckpt['best_acc']:.4f})")
    return model


@torch.no_grad()
def run_inference(model, dataloader, device):
    """Returns (all_preds, all_labels, all_confidences, all_filepaths)."""
    model.eval()
    all_preds, all_labels, all_confs, all_paths = [], [], [], []

    # dataset.samples gives us (filepath, label) in the same order ImageFolder
    # iterates, which lets us trace predictions back to specific image files.
    filepaths = [p for p, _ in dataloader.dataset.samples]
    idx = 0

    for images, labels in dataloader:
        images = images.to(device)
        outputs = model(images)
        probs = torch.softmax(outputs, dim=1)
        confs, preds = probs.max(dim=1)

        batch_size = images.size(0)
        all_paths.extend(filepaths[idx: idx + batch_size])
        idx += batch_size

        all_preds.extend(preds.cpu().tolist())
        all_labels.extend(labels.tolist())
        all_confs.extend(confs.cpu().tolist())

    return all_preds, all_labels, all_confs, all_paths


def plot_confusion_matrix(labels, preds, class_names, output_path):
    cm = confusion_matrix(labels, preds)
    plt.figure(figsize=(max(10, len(class_names) * 0.5), max(8, len(class_names) * 0.5)))
    sns.heatmap(cm, annot=len(class_names) <= 20, fmt="d", cmap="Blues",
                xticklabels=class_names, yticklabels=class_names)
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.title("Confusion Matrix (Test Set)")
    plt.xticks(rotation=90)
    plt.yticks(rotation=0)
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150)
    print(f"Confusion matrix saved to {output_path}")


def save_misclassified(preds, labels, confs, filepaths, class_names, output_path):
    rows = []
    for pred, label, conf, path in zip(preds, labels, confs, filepaths):
        if pred != label:
            rows.append({
                "filepath": path,
                "true_label": class_names[label],
                "predicted_label": class_names[pred],
                "confidence": round(conf, 4),
            })
    df = pd.DataFrame(rows).sort_values("confidence", ascending=False)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"{len(df)} misclassified examples saved to {output_path}")
    if len(df) > 0:
        print("\nTop 5 highest-confidence mistakes (worth a visual/Grad-CAM look):")
        print(df.head(5).to_string(index=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default="outputs/checkpoints/best.pt")
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument("--output_dir", default="outputs/predictions")
    args = parser.parse_args()

    config = yaml.safe_load(open(args.config))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Build test dataset/loader directly (not via build_dataloaders_from_config)
    # since we only need the test split here, not train/val too.
    image_size = config["training"]["image_size"]
    test_transform = get_transforms("test", image_size=image_size)
    test_dataset = build_dataset(config["dataset"]["root"], "test", transform=test_transform)
    test_loader = build_dataloader(
        test_dataset, split="test",
        batch_size=config["training"]["batch_size"],
        num_workers=config.get("dataset", {}).get("num_workers", 4),
        pin_memory=(device.type == "cuda"),
    )
    class_names = test_dataset.classes
    print(f"Test set: {len(test_dataset)} images across {len(class_names)} classes")

    model = build_model(config, num_classes=len(class_names)).to(device)
    model = load_checkpoint(model, args.checkpoint, device)

    preds, labels, confs, filepaths = run_inference(model, test_loader, device)

    print("\n=== Classification Report (Test Set) ===")
    report = classification_report(labels, preds, target_names=class_names, zero_division=0)
    print(report)

    with open(os.path.join(args.output_dir, "classification_report.txt"), "w") as f:
        f.write(report)

    plot_confusion_matrix(
        labels, preds, class_names,
        os.path.join(args.output_dir, "confusion_matrix.png"),
    )
    save_misclassified(
        preds, labels, confs, filepaths, class_names,
        os.path.join(args.output_dir, "misclassified.csv"),
    )

    test_acc = sum(p == l for p, l in zip(preds, labels)) / len(labels)
    print(f"\nFinal TEST accuracy: {test_acc:.4f}")
    print("Compare this to your reported val_acc — a large gap (val much higher than "
          "test) would indicate the val number was inflated (e.g. by leakage); "
          "a close match supports the number being genuine.")


if __name__ == "__main__":
    main()
