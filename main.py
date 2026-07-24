"""
main.py

Entry point: builds data loaders, model, optimizer, and runs the two-stage
transfer learning process (frozen backbone -> fine-tune).

Usage:
    python main.py
"""

import yaml
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR

from data.dataloader import build_dataloaders_from_config
from models.model import build_model
from engine.trainer import Trainer


def main():
    config = yaml.safe_load(open("configs/config.yaml"))

    torch.manual_seed(config["seed"])

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # ---- Data ----
    loaders = build_dataloaders_from_config(config, config["dataset"]["root"])
    train_loader, val_loader = loaders["train"], loaders["val"]
    num_classes = train_loader.dataset.num_classes
    print(f"Classes ({num_classes}): {train_loader.dataset.classes}")

    # ---- Model ----
    model = build_model(config, num_classes=num_classes).to(device)
    criterion = nn.CrossEntropyLoss()

    checkpoint_dir = config["output"]["checkpoint_dir"]
    log_dir = config["output"].get("log_dir", "outputs/logs")

    # Stage-specific epoch/LR config, with sensible fallbacks if not yet added to config.yaml
    stage1_epochs = config["training"].get("stage1_epochs", 5)
    stage2_epochs = config["training"].get("stage2_epochs", config["training"]["epochs"] - stage1_epochs)
    stage1_lr = config["training"].get("stage1_lr", config["training"]["learning_rate"])
    stage2_lr = config["training"].get("stage2_lr", config["training"]["learning_rate"] / 10)

    # ---- Stage 1: frozen backbone, train classifier head ----
    print("\n=== Stage 1: training classifier head (backbone frozen) ===")
    model.freeze_backbone()
    optimizer = AdamW(model.get_trainable_params(), lr=stage1_lr)
    scheduler = CosineAnnealingLR(optimizer, T_max=stage1_epochs)

    trainer = Trainer(model, optimizer, criterion, device, checkpoint_dir, log_dir)
    trainer.fit(train_loader, val_loader, epochs=stage1_epochs, stage_name="stage1",
                scheduler=scheduler)

    # ---- Stage 2: unfreeze, fine-tune end-to-end at lower LR ----
    print("\n=== Stage 2: fine-tuning full network ===")
    model.unfreeze_backbone()
    optimizer = AdamW(model.get_trainable_params(), lr=stage2_lr)
    scheduler = CosineAnnealingLR(optimizer, T_max=stage2_epochs)

    trainer.optimizer = optimizer  # swap optimizer, keep same trainer (checkpointing, best_acc)
    trainer.fit(train_loader, val_loader, epochs=stage2_epochs, stage_name="stage2",
                scheduler=scheduler)

    trainer.close()
    print(f"\nTraining complete. Best val_acc={trainer.best_acc:.4f}")
    print(f"Best checkpoint saved to {checkpoint_dir}/best.pt")


if __name__ == "__main__":
    main()
