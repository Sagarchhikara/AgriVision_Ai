"""
engine/trainer.py

Training and evaluation loops, checkpointing, and TensorBoard logging.

Design notes
------------
- train_one_epoch/evaluate are separated from the outer loop (in main.py) so
  each is independently testable and reusable (e.g. evaluate() will be reused
  as-is when you build the standalone evaluation script in Phase 1.5).
- Checkpointing saves `best.pt` only when val accuracy improves, plus `last.pt`
  every epoch for resuming an interrupted run — avoids accumulating 20 epoch
  checkpoints for a 15-class problem where only the best one matters.
- All metrics are computed with sklearn on accumulated predictions/labels
  rather than running averages, so precision/recall/F1 are exact, not
  batch-averaged approximations.
"""

import os
import time
import torch
from sklearn.metrics import accuracy_score, precision_recall_fscore_support


def train_one_epoch(model, dataloader, optimizer, criterion, device):
    model.train()
    running_loss = 0.0
    all_preds, all_labels = [], []

    for images, labels in dataloader:
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)
        preds = outputs.argmax(dim=1)
        all_preds.extend(preds.cpu().tolist())
        all_labels.extend(labels.cpu().tolist())

    epoch_loss = running_loss / len(dataloader.dataset)
    epoch_acc = accuracy_score(all_labels, all_preds)
    return epoch_loss, epoch_acc


@torch.no_grad()
def evaluate(model, dataloader, criterion, device):
    model.eval()
    running_loss = 0.0
    all_preds, all_labels = [], []

    for images, labels in dataloader:
        images, labels = images.to(device), labels.to(device)
        outputs = model(images)
        loss = criterion(outputs, labels)

        running_loss += loss.item() * images.size(0)
        preds = outputs.argmax(dim=1)
        all_preds.extend(preds.cpu().tolist())
        all_labels.extend(labels.cpu().tolist())

    epoch_loss = running_loss / len(dataloader.dataset)
    epoch_acc = accuracy_score(all_labels, all_preds)
    precision, recall, f1, _ = precision_recall_fscore_support(
        all_labels, all_preds, average="macro", zero_division=0
    )
    metrics = {
        "loss": epoch_loss,
        "accuracy": epoch_acc,
        "precision_macro": precision,
        "recall_macro": recall,
        "f1_macro": f1,
    }
    return metrics


def save_checkpoint(model, optimizer, epoch, best_acc, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    torch.save({
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "best_acc": best_acc,
    }, path)


class Trainer:
    """
    Orchestrates the full training loop across both transfer-learning stages,
    with checkpointing and TensorBoard logging. main.py just constructs this
    and calls .fit(); all epoch bookkeeping lives here.
    """

    def __init__(self, model, optimizer, criterion, device, checkpoint_dir, log_dir):
        self.model = model
        self.optimizer = optimizer
        self.criterion = criterion
        self.device = device
        self.checkpoint_dir = checkpoint_dir
        self.best_acc = 0.0

        from torch.utils.tensorboard import SummaryWriter
        self.writer = SummaryWriter(log_dir=log_dir)

    def fit(self, train_loader, val_loader, epochs, stage_name="stage", scheduler=None):
        for epoch in range(1, epochs + 1):
            start = time.time()

            train_loss, train_acc = train_one_epoch(
                self.model, train_loader, self.optimizer, self.criterion, self.device
            )
            val_metrics = evaluate(self.model, val_loader, self.criterion, self.device)

            elapsed = time.time() - start
            print(
                f"[{stage_name}] Epoch {epoch}/{epochs} "
                f"| train_loss={train_loss:.4f} train_acc={train_acc:.4f} "
                f"| val_loss={val_metrics['loss']:.4f} val_acc={val_metrics['accuracy']:.4f} "
                f"val_f1={val_metrics['f1_macro']:.4f} | {elapsed:.1f}s"
            )

            self.writer.add_scalar(f"{stage_name}/train_loss", train_loss, epoch)
            self.writer.add_scalar(f"{stage_name}/train_acc", train_acc, epoch)
            self.writer.add_scalar(f"{stage_name}/val_loss", val_metrics["loss"], epoch)
            self.writer.add_scalar(f"{stage_name}/val_acc", val_metrics["accuracy"], epoch)
            self.writer.add_scalar(f"{stage_name}/val_f1_macro", val_metrics["f1_macro"], epoch)

            save_checkpoint(
                self.model, self.optimizer, epoch, self.best_acc,
                os.path.join(self.checkpoint_dir, "last.pt"),
            )

            if val_metrics["accuracy"] > self.best_acc:
                self.best_acc = val_metrics["accuracy"]
                save_checkpoint(
                    self.model, self.optimizer, epoch, self.best_acc,
                    os.path.join(self.checkpoint_dir, "best.pt"),
                )
                print(f"  -> new best val_acc={self.best_acc:.4f}, saved best.pt")

            if scheduler is not None:
                scheduler.step()

    def close(self):
        self.writer.close()
