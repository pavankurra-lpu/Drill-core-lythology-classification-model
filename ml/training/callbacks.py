"""
ml/training/callbacks.py
-------------------------
Training callbacks: EarlyStopping, ModelCheckpoint, LearningRateScheduler.

Each callback exposes:
  on_epoch_end(trainer, epoch, metrics) → Optional[bool]
    Returns True if training should stop (EarlyStopping only).
"""

from __future__ import annotations

import logging
import math
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import torch

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Base callback
# ---------------------------------------------------------------------------

class Callback:
    """Abstract base class — override the hooks you need."""

    def on_train_begin(self, trainer: Any) -> None:
        pass

    def on_train_end(self, trainer: Any) -> None:
        pass

    def on_epoch_begin(self, trainer: Any, epoch: int) -> None:
        pass

    def on_epoch_end(
        self,
        trainer: Any,
        epoch: int,
        metrics: Dict[str, float],
    ) -> Optional[bool]:
        """Return True to stop training early."""
        return None

    def on_batch_end(
        self,
        trainer: Any,
        batch_idx: int,
        metrics: Dict[str, float],
    ) -> None:
        pass


# ---------------------------------------------------------------------------
# EarlyStopping
# ---------------------------------------------------------------------------

class EarlyStopping(Callback):
    """
    Stop training when a monitored metric stops improving.

    Parameters
    ----------
    monitor : str
        Metric name to watch (e.g. 'val_loss', 'val_acc').
    patience : int
        Number of epochs to wait after last improvement.
    min_delta : float
        Minimum change to qualify as an improvement.
    mode : str
        'min' (lower is better) or 'max' (higher is better).
        Automatically inferred from *monitor* if set to 'auto'.
    restore_best_weights : bool
        If True, the trainer's model state is reverted to the best
        epoch's weights when early stopping triggers.
    verbose : bool
        Log messages when patience counter changes.
    """

    def __init__(
        self,
        monitor: str = "val_loss",
        patience: int = 10,
        min_delta: float = 1e-4,
        mode: str = "auto",
        restore_best_weights: bool = True,
        verbose: bool = True,
    ) -> None:
        self.monitor = monitor
        self.patience = patience
        self.min_delta = abs(min_delta)
        self.restore_best_weights = restore_best_weights
        self.verbose = verbose

        # Infer mode
        if mode == "auto":
            self.mode = "min" if "loss" in monitor.lower() else "max"
        else:
            assert mode in ("min", "max"), "mode must be 'min', 'max', or 'auto'."
            self.mode = mode

        self._best_value: float = math.inf if self.mode == "min" else -math.inf
        self._counter: int = 0
        self._best_weights: Optional[Dict] = None
        self._stopped_epoch: int = 0

    # ------------------------------------------------------------------ #

    def _is_improvement(self, current: float) -> bool:
        if self.mode == "min":
            return current < self._best_value - self.min_delta
        return current > self._best_value + self.min_delta

    def on_epoch_end(
        self,
        trainer: Any,
        epoch: int,
        metrics: Dict[str, float],
    ) -> Optional[bool]:
        current = metrics.get(self.monitor)
        if current is None:
            logger.warning(
                "EarlyStopping: metric '%s' not found in metrics dict. "
                "Available: %s",
                self.monitor, list(metrics.keys()),
            )
            return None

        if self._is_improvement(current):
            self._best_value = current
            self._counter = 0
            if self.restore_best_weights and trainer is not None:
                import copy
                self._best_weights = copy.deepcopy(trainer.model.state_dict())
            if self.verbose:
                logger.info(
                    "EarlyStopping: %s improved to %.6f.", self.monitor, current
                )
        else:
            self._counter += 1
            if self.verbose:
                logger.info(
                    "EarlyStopping: %s did not improve (%.6f). "
                    "Counter: %d / %d.",
                    self.monitor, current, self._counter, self.patience,
                )

        if self._counter >= self.patience:
            self._stopped_epoch = epoch
            logger.info(
                "EarlyStopping triggered at epoch %d. Best %s: %.6f.",
                epoch, self.monitor, self._best_value,
            )
            if self.restore_best_weights and self._best_weights is not None:
                trainer.model.load_state_dict(self._best_weights)
                logger.info("Restored best model weights.")
            return True   # signal to stop

        return None

    @property
    def best_value(self) -> float:
        return self._best_value

    @property
    def stopped_epoch(self) -> int:
        return self._stopped_epoch


# ---------------------------------------------------------------------------
# ModelCheckpoint
# ---------------------------------------------------------------------------

class ModelCheckpoint(Callback):
    """
    Save model checkpoints when a monitored metric improves.

    Parameters
    ----------
    dirpath : str or Path
        Directory to save checkpoint files.
    filename : str
        Filename template. Use ``{epoch}``, ``{monitor}``,
        ``{val_loss:.4f}``, etc. as placeholders.
    monitor : str
        Metric name to watch.
    mode : str
        'min' or 'max' or 'auto'.
    save_top_k : int
        Keep only the top-k checkpoints (oldest are deleted). -1 = keep all.
    save_last : bool
        Always save the last epoch's checkpoint as ``last.pth``.
    verbose : bool
        Log checkpoint events.
    """

    def __init__(
        self,
        dirpath: Union[str, Path] = "checkpoints",
        filename: str = "epoch{epoch:03d}_{monitor:.4f}",
        monitor: str = "val_loss",
        mode: str = "auto",
        save_top_k: int = 3,
        save_last: bool = True,
        verbose: bool = True,
    ) -> None:
        self.dirpath = Path(dirpath)
        self.dirpath.mkdir(parents=True, exist_ok=True)
        self.filename = filename
        self.monitor = monitor
        self.save_top_k = save_top_k
        self.save_last = save_last
        self.verbose = verbose

        if mode == "auto":
            self.mode = "min" if "loss" in monitor.lower() else "max"
        else:
            assert mode in ("min", "max")
            self.mode = mode

        self._best_value: float = math.inf if self.mode == "min" else -math.inf
        self._saved_checkpoints: list = []   # list of (metric_value, filepath)

    # ------------------------------------------------------------------ #

    def _is_improvement(self, current: float) -> bool:
        if self.mode == "min":
            return current < self._best_value
        return current > self._best_value

    def on_epoch_end(
        self,
        trainer: Any,
        epoch: int,
        metrics: Dict[str, float],
    ) -> Optional[bool]:
        current = metrics.get(self.monitor)

        # Always save last
        if self.save_last and trainer is not None:
            last_path = self.dirpath / "last.pth"
            self._save(trainer, epoch, metrics, last_path)

        if current is None:
            return None

        if self._is_improvement(current):
            self._best_value = current

            # Compose filename
            safe_monitor = f"{current:.4f}"
            fname = (
                self.filename
                .replace("{epoch}", f"{epoch:03d}")
                .replace("{monitor}", safe_monitor)
                + ".pth"
            )
            save_path = self.dirpath / fname

            if trainer is not None:
                self._save(trainer, epoch, metrics, save_path)

            self._saved_checkpoints.append((current, save_path))
            self._saved_checkpoints.sort(key=lambda x: x[0],
                                         reverse=(self.mode == "max"))

            # Prune old checkpoints
            if self.save_top_k > 0:
                while len(self._saved_checkpoints) > self.save_top_k:
                    _, old_path = self._saved_checkpoints.pop()
                    if old_path.exists():
                        old_path.unlink()
                        logger.debug("Removed old checkpoint '%s'.", old_path)

            if self.verbose:
                logger.info(
                    "ModelCheckpoint: saved '%s' (%s=%.6f).",
                    save_path.name, self.monitor, current,
                )

        return None

    @staticmethod
    def _save(
        trainer: Any,
        epoch: int,
        metrics: Dict[str, float],
        path: Path,
    ) -> None:
        """Persist the trainer's model + optimiser state to *path*."""
        checkpoint = {
            "epoch": epoch,
            "model_state_dict": trainer.model.state_dict(),
            "metrics": metrics,
        }
        if hasattr(trainer, "optimizer"):
            checkpoint["optimizer_state_dict"] = trainer.optimizer.state_dict()
        if hasattr(trainer, "scheduler") and trainer.scheduler is not None:
            checkpoint["scheduler_state_dict"] = trainer.scheduler.state_dict()
        torch.save(checkpoint, path)

    @property
    def best_model_path(self) -> Optional[Path]:
        if not self._saved_checkpoints:
            return None
        return self._saved_checkpoints[0][1]

    @property
    def best_value(self) -> float:
        return self._best_value


# ---------------------------------------------------------------------------
# LearningRateScheduler
# ---------------------------------------------------------------------------

class LearningRateScheduler(Callback):
    """
    Wrapper that calls a PyTorch LR scheduler each epoch and logs the
    current learning rate.

    Parameters
    ----------
    scheduler : torch.optim.lr_scheduler._LRScheduler
        Any PyTorch LR scheduler.  For ReduceLROnPlateau, pass the
        monitored metric via ``monitor``.
    monitor : str, optional
        Metric name passed to ReduceLROnPlateau.step(metric).
    verbose : bool
        Log LR after every scheduler step.
    """

    def __init__(
        self,
        scheduler: Any,
        monitor: str = "val_loss",
        verbose: bool = True,
    ) -> None:
        self.scheduler = scheduler
        self.monitor = monitor
        self.verbose = verbose

    def on_epoch_end(
        self,
        trainer: Any,
        epoch: int,
        metrics: Dict[str, float],
    ) -> Optional[bool]:
        if self.scheduler is None:
            return None

        # ReduceLROnPlateau needs a metric value
        is_plateau = isinstance(
            self.scheduler,
            torch.optim.lr_scheduler.ReduceLROnPlateau,
        )
        if is_plateau:
            metric_val = metrics.get(self.monitor, None)
            if metric_val is not None:
                self.scheduler.step(metric_val)
        else:
            self.scheduler.step()

        if self.verbose:
            try:
                current_lr = self.scheduler.get_last_lr()
            except AttributeError:
                current_lr = [pg["lr"] for pg in self.scheduler.optimizer.param_groups]
            logger.info("LRScheduler: epoch %d LR = %s.", epoch, current_lr)

        return None

    def get_lr(self) -> list:
        try:
            return self.scheduler.get_last_lr()
        except AttributeError:
            return [pg["lr"] for pg in self.scheduler.optimizer.param_groups]
