"""
ml/training/trainer.py
-----------------------
Full training pipeline for the Lithology Classification System.

Features
--------
* Per-epoch train / validation loop with AMP (torch.cuda.amp)
* Gradient clipping
* Pluggable callback system (EarlyStopping, ModelCheckpoint, LRScheduler)
* TensorBoard logging (loss, accuracy, LR, gradient norms)
* Class-weighted cross-entropy loss
* Checkpoint save / restore
* Top-1 and Top-5 accuracy tracking
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import torch
import torch.nn as nn
import torch.optim as optim
from torch.cuda.amp import GradScaler, autocast
from torch.optim.lr_scheduler import (
    CosineAnnealingLR,
    OneCycleLR,
    ReduceLROnPlateau,
    StepLR,
)
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter

from ml.training.callbacks import (
    Callback,
    EarlyStopping,
    LearningRateScheduler,
    ModelCheckpoint,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Accuracy helpers
# ---------------------------------------------------------------------------

def _top_k_accuracy(
    logits: torch.Tensor,
    labels: torch.Tensor,
    k: int = 1,
) -> float:
    """Compute top-k accuracy for a batch."""
    with torch.no_grad():
        batch_size = labels.size(0)
        _, pred = logits.topk(k, dim=1, largest=True, sorted=True)
        pred = pred.t()
        correct = pred.eq(labels.view(1, -1).expand_as(pred))
        correct_k = correct[:k].reshape(-1).float().sum(0)
        return (correct_k / batch_size).item()


# ---------------------------------------------------------------------------
# Trainer
# ---------------------------------------------------------------------------

class LithologyTrainer:
    """
    End-to-end trainer for lithology classification models.

    Parameters
    ----------
    model : nn.Module
        The model to train.
    config : object
        Configuration object (or dict) with fields:
            training.learning_rate, training.weight_decay,
            training.optimizer, training.grad_clip,
            training.use_amp, training.scheduler,
            training.T_max, training.step_size, training.gamma,
            training.patience_lr, training.num_epochs,
            training.tensorboard_dir, training.early_stopping_patience,
            training.early_stopping_min_delta, training.monitor,
            model.checkpoint_dir, model.best_model_filename.
    train_loader : DataLoader
    val_loader : DataLoader
    class_weights : torch.Tensor, optional
        Per-class weights for the cross-entropy loss.
    device : torch.device, optional
        Defaults to CUDA if available, else CPU.
    callbacks : List[Callback], optional
        Extra callbacks (added on top of EarlyStopping / ModelCheckpoint
        which are built from config).
    """

    def __init__(
        self,
        model: nn.Module,
        config: Any,
        train_loader: DataLoader,
        val_loader: DataLoader,
        class_weights: Optional[torch.Tensor] = None,
        device: Optional[torch.device] = None,
        callbacks: Optional[List[Callback]] = None,
    ) -> None:
        # ── Device ──────────────────────────────────────────────────────── #
        if device is None:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.device = device

        self.model = model.to(device)
        self.config = config
        self.train_loader = train_loader
        self.val_loader = val_loader

        # ── Training config (support both dataclass and dict) ────────────── #
        tc = getattr(config, "training", config)  # TrainingConfig or dict-like
        mc = getattr(config, "model", config)

        def _get(obj: Any, key: str, default: Any = None) -> Any:
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        self._lr = _get(tc, "learning_rate", 1e-4)
        self._wd = _get(tc, "weight_decay", 1e-5)
        self._opt_name = _get(tc, "optimizer", "adamw")
        self._grad_clip = _get(tc, "grad_clip", 1.0)
        self._use_amp = _get(tc, "use_amp", True) and device.type == "cuda"
        self._sched_name = _get(tc, "scheduler", "cosine")
        self._T_max = _get(tc, "T_max", 50)
        self._step_size = _get(tc, "step_size", 10)
        self._gamma = _get(tc, "gamma", 0.1)
        self._patience_lr = _get(tc, "patience_lr", 5)
        self._num_epochs = _get(tc, "num_epochs", 50)
        self._log_interval = _get(tc, "log_interval", 10)
        self._tb_dir = _get(tc, "tensorboard_dir", "runs")
        self._es_patience = _get(tc, "early_stopping_patience", 10)
        self._es_min_delta = _get(tc, "early_stopping_min_delta", 1e-4)
        self._monitor = _get(tc, "monitor", "val_loss")
        self._ckpt_dir = _get(mc, "checkpoint_dir", "checkpoints")
        self._best_fname = _get(mc, "best_model_filename", "best_model.pth")
        self._warmup_epochs = _get(tc, "warmup_epochs", 3)

        # ── Loss function ─────────────────────────────────────────────── #
        if class_weights is not None:
            class_weights = class_weights.to(device)
        self.criterion = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=0.1)

        # ── Optimiser ─────────────────────────────────────────────────── #
        self.optimizer = self._build_optimizer()

        # ── LR Scheduler ──────────────────────────────────────────────── #
        self.scheduler = self._build_scheduler()

        # ── AMP scaler ────────────────────────────────────────────────── #
        self.scaler = GradScaler(enabled=self._use_amp)

        # ── TensorBoard ───────────────────────────────────────────────── #
        Path(self._tb_dir).mkdir(parents=True, exist_ok=True)
        self.writer = SummaryWriter(log_dir=self._tb_dir)

        # ── Callbacks ─────────────────────────────────────────────────── #
        self.callbacks: List[Callback] = callbacks or []
        # Auto-add early stopping and checkpoint
        self.early_stopping = EarlyStopping(
            monitor=self._monitor,
            patience=self._es_patience,
            min_delta=self._es_min_delta,
        )
        self.checkpoint = ModelCheckpoint(
            dirpath=self._ckpt_dir,
            monitor=self._monitor,
            filename=f"epoch{{epoch}}_{self._monitor}{{monitor}}",
            save_top_k=3,
            save_last=True,
        )
        self.callbacks = [self.early_stopping, self.checkpoint] + self.callbacks
        if self.scheduler is not None:
            self.callbacks.append(
                LearningRateScheduler(self.scheduler, monitor=self._monitor)
            )

        # ── Training history ──────────────────────────────────────────── #
        self.history: Dict[str, List[float]] = {
            "train_loss": [],
            "train_acc": [],
            "val_loss": [],
            "val_acc": [],
            "lr": [],
        }
        self.best_val_loss: float = float("inf")
        self.best_val_acc: float = 0.0
        self.current_epoch: int = 0

        logger.info(
            "LithologyTrainer | device=%s | amp=%s | optimizer=%s | scheduler=%s",
            device, self._use_amp, self._opt_name, self._sched_name,
        )

    # ---------------------------------------------------------------------- #
    # Build optimiser / scheduler                                              #
    # ---------------------------------------------------------------------- #

    def _build_optimizer(self) -> optim.Optimizer:
        name = self._opt_name.lower()
        if name == "adamw":
            return optim.AdamW(
                self.model.parameters(),
                lr=self._lr,
                weight_decay=self._wd,
            )
        elif name == "adam":
            return optim.Adam(
                self.model.parameters(),
                lr=self._lr,
                weight_decay=self._wd,
            )
        elif name == "sgd":
            return optim.SGD(
                self.model.parameters(),
                lr=self._lr,
                momentum=0.9,
                weight_decay=self._wd,
                nesterov=True,
            )
        else:
            raise ValueError(f"Unknown optimizer: '{self._opt_name}'.")

    def _build_scheduler(self) -> Optional[Any]:
        name = self._sched_name.lower()
        if name == "cosine":
            return CosineAnnealingLR(
                self.optimizer,
                T_max=self._T_max,
                eta_min=self._lr * 1e-2,
            )
        elif name == "step":
            return StepLR(
                self.optimizer,
                step_size=self._step_size,
                gamma=self._gamma,
            )
        elif name in ("plateau", "reduce"):
            return ReduceLROnPlateau(
                self.optimizer,
                mode="min" if "loss" in self._monitor else "max",
                factor=self._gamma,
                patience=self._patience_lr,
                verbose=True,
            )
        elif name in ("none", ""):
            return None
        else:
            raise ValueError(f"Unknown scheduler: '{self._sched_name}'.")

    # ---------------------------------------------------------------------- #
    # Single-epoch routines                                                    #
    # ---------------------------------------------------------------------- #

    def train_epoch(self, epoch: int) -> Dict[str, float]:
        """Run one training epoch. Returns loss and accuracy."""
        self.model.train()

        total_loss = 0.0
        total_correct = 0
        total_samples = 0
        start = time.time()

        for batch_idx, (images, labels) in enumerate(self.train_loader):
            images = images.to(self.device, non_blocking=True)
            labels = labels.to(self.device, non_blocking=True)

            self.optimizer.zero_grad(set_to_none=True)

            with autocast(enabled=self._use_amp):
                logits = self.model(images)
                loss = self.criterion(logits, labels)

            self.scaler.scale(loss).backward()

            # Gradient clipping
            if self._grad_clip > 0:
                self.scaler.unscale_(self.optimizer)
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(), self._grad_clip
                )

            self.scaler.step(self.optimizer)
            self.scaler.update()

            # Metrics
            batch_size = labels.size(0)
            _, predicted = logits.detach().max(1)
            total_correct += predicted.eq(labels).sum().item()
            total_samples += batch_size
            total_loss += loss.item() * batch_size

            if (batch_idx + 1) % self._log_interval == 0:
                running_loss = total_loss / total_samples
                running_acc = total_correct / total_samples
                logger.info(
                    "[Epoch %d | Step %d/%d] loss=%.4f acc=%.4f",
                    epoch, batch_idx + 1, len(self.train_loader),
                    running_loss, running_acc,
                )

        elapsed = time.time() - start
        avg_loss = total_loss / max(total_samples, 1)
        avg_acc = total_correct / max(total_samples, 1)

        logger.info(
            "Train epoch %d | loss=%.4f | acc=%.4f | time=%.1fs",
            epoch, avg_loss, avg_acc, elapsed,
        )
        return {"train_loss": avg_loss, "train_acc": avg_acc}

    @torch.no_grad()
    def validate_epoch(self, epoch: int) -> Dict[str, float]:
        """Run one validation pass. Returns loss and accuracy."""
        self.model.eval()

        total_loss = 0.0
        total_correct = 0
        total_correct_top5 = 0
        total_samples = 0
        start = time.time()

        for images, labels in self.val_loader:
            images = images.to(self.device, non_blocking=True)
            labels = labels.to(self.device, non_blocking=True)

            with autocast(enabled=self._use_amp):
                logits = self.model(images)
                loss = self.criterion(logits, labels)

            batch_size = labels.size(0)
            _, predicted = logits.max(1)
            total_correct += predicted.eq(labels).sum().item()
            total_correct_top5 += int(
                _top_k_accuracy(logits, labels, k=min(5, logits.size(1))) * batch_size
            )
            total_samples += batch_size
            total_loss += loss.item() * batch_size

        elapsed = time.time() - start
        avg_loss = total_loss / max(total_samples, 1)
        avg_acc = total_correct / max(total_samples, 1)
        avg_acc_top5 = total_correct_top5 / max(total_samples, 1)

        logger.info(
            "Val   epoch %d | loss=%.4f | acc=%.4f | top5=%.4f | time=%.1fs",
            epoch, avg_loss, avg_acc, avg_acc_top5, elapsed,
        )
        return {
            "val_loss": avg_loss,
            "val_acc": avg_acc,
            "val_acc_top5": avg_acc_top5,
        }

    # ---------------------------------------------------------------------- #
    # Full training loop                                                       #
    # ---------------------------------------------------------------------- #

    def train(self, num_epochs: Optional[int] = None) -> Dict[str, List[float]]:
        """
        Run the complete training loop.

        Parameters
        ----------
        num_epochs : int, optional
            Override config's num_epochs.

        Returns
        -------
        dict
            Training history with keys: train_loss, train_acc, val_loss,
            val_acc, lr.
        """
        n_epochs = num_epochs or self._num_epochs

        # Notify callbacks of training start
        for cb in self.callbacks:
            cb.on_train_begin(self)

        logger.info("=" * 60)
        logger.info("Starting training: %d epochs | device=%s", n_epochs, self.device)
        logger.info("=" * 60)

        for epoch in range(1, n_epochs + 1):
            self.current_epoch = epoch

            for cb in self.callbacks:
                cb.on_epoch_begin(self, epoch)

            # ── Train ───────────────────────────────────────────────────── #
            train_metrics = self.train_epoch(epoch)

            # ── Validate ─────────────────────────────────────────────────── #
            val_metrics = self.validate_epoch(epoch)

            # ── Collect metrics ──────────────────────────────────────────── #
            current_lr = self.optimizer.param_groups[0]["lr"]
            metrics = {**train_metrics, **val_metrics, "lr": current_lr}

            # ── Update history ───────────────────────────────────────────── #
            self.history["train_loss"].append(train_metrics["train_loss"])
            self.history["train_acc"].append(train_metrics["train_acc"])
            self.history["val_loss"].append(val_metrics["val_loss"])
            self.history["val_acc"].append(val_metrics["val_acc"])
            self.history["lr"].append(current_lr)

            # ── TensorBoard logging ──────────────────────────────────────── #
            self._log_tensorboard(epoch, metrics)

            # ── Best model ───────────────────────────────────────────────── #
            if val_metrics["val_loss"] < self.best_val_loss:
                self.best_val_loss = val_metrics["val_loss"]
                self.save_checkpoint(
                    epoch,
                    val_metrics["val_loss"],
                    val_metrics["val_acc"],
                    filename="best_model.pth",
                )
                logger.info(
                    "★ New best val_loss=%.4f at epoch %d", self.best_val_loss, epoch
                )
            if val_metrics["val_acc"] > self.best_val_acc:
                self.best_val_acc = val_metrics["val_acc"]

            # ── Callbacks ────────────────────────────────────────────────── #
            stop = False
            for cb in self.callbacks:
                result = cb.on_epoch_end(self, epoch, metrics)
                if result is True:
                    stop = True

            if stop:
                logger.info("Early stopping at epoch %d.", epoch)
                break

        logger.info("=" * 60)
        logger.info(
            "Training finished. Best val_loss=%.4f | Best val_acc=%.4f",
            self.best_val_loss, self.best_val_acc,
        )
        logger.info("=" * 60)

        # Notify callbacks of training end
        for cb in self.callbacks:
            cb.on_train_end(self)

        self.writer.close()
        return self.history

    # ---------------------------------------------------------------------- #
    # TensorBoard                                                              #
    # ---------------------------------------------------------------------- #

    def _log_tensorboard(self, epoch: int, metrics: Dict[str, float]) -> None:
        for key, val in metrics.items():
            group = key.split("_")[0]   # "train" or "val"
            metric_name = "_".join(key.split("_")[1:]) if "_" in key else key
            self.writer.add_scalar(f"{group}/{metric_name}", val, epoch)

        # Log gradient norm
        total_norm = 0.0
        for p in self.model.parameters():
            if p.grad is not None:
                total_norm += p.grad.data.norm(2).item() ** 2
        self.writer.add_scalar("train/grad_norm", total_norm ** 0.5, epoch)

    # ---------------------------------------------------------------------- #
    # Checkpoint I/O                                                           #
    # ---------------------------------------------------------------------- #

    def save_checkpoint(
        self,
        epoch: int,
        val_loss: float,
        val_acc: float,
        filename: Optional[str] = None,
    ) -> str:
        """Save model + optimiser + scheduler state to disk."""
        Path(self._ckpt_dir).mkdir(parents=True, exist_ok=True)
        fname = filename or f"epoch_{epoch:03d}_loss{val_loss:.4f}.pth"
        path = str(Path(self._ckpt_dir) / fname)

        checkpoint = {
            "epoch": epoch,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "val_loss": val_loss,
            "val_acc": val_acc,
            "history": self.history,
        }
        if self.scheduler is not None:
            checkpoint["scheduler_state_dict"] = self.scheduler.state_dict()

        torch.save(checkpoint, path)
        logger.debug("Checkpoint saved to '%s'.", path)
        return path

    def load_checkpoint(self, path: str) -> int:
        """
        Restore model + optimiser + scheduler from a checkpoint file.

        Returns
        -------
        int
            The epoch at which the checkpoint was saved.
        """
        checkpoint = torch.load(path, map_location=self.device)

        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])

        if "scheduler_state_dict" in checkpoint and self.scheduler is not None:
            self.scheduler.load_state_dict(checkpoint["scheduler_state_dict"])

        if "history" in checkpoint:
            self.history = checkpoint["history"]

        epoch = checkpoint.get("epoch", 0)
        logger.info("Loaded checkpoint from '%s' (epoch %d).", path, epoch)
        return epoch

    # ---------------------------------------------------------------------- #
    # Convenience                                                              #
    # ---------------------------------------------------------------------- #

    def get_lr(self) -> float:
        return self.optimizer.param_groups[0]["lr"]

    def __repr__(self) -> str:
        return (
            f"LithologyTrainer("
            f"model={self.model.__class__.__name__}, "
            f"device={self.device}, "
            f"optimizer={self._opt_name}, "
            f"scheduler={self._sched_name})"
        )
