"""
ml/utils/helpers.py
--------------------
Utility functions shared across the ML pipeline.
"""

from __future__ import annotations

import json
import logging
import os
import random
from pathlib import Path
from typing import Dict, List, Optional, Union

import numpy as np
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------

def set_seed(seed: int = 42) -> None:
    """
    Set global random seeds for reproducibility across Python, NumPy,
    and PyTorch (CPU + all CUDA devices).

    Parameters
    ----------
    seed : int
        The seed value to use.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    os.environ["PYTHONHASHSEED"] = str(seed)
    logger.debug("Global seed set to %d.", seed)


# ---------------------------------------------------------------------------
# Device
# ---------------------------------------------------------------------------

def get_device(device_str: str = "auto") -> torch.device:
    """
    Resolve the compute device.

    Parameters
    ----------
    device_str : str
        'auto'  → CUDA if available, else MPS, else CPU.
        'cuda'  → CUDA (raises if not available).
        'mps'   → Apple MPS (raises if not available).
        'cpu'   → CPU.

    Returns
    -------
    torch.device
    """
    if device_str == "auto":
        if torch.cuda.is_available():
            device = torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = torch.device("mps")
        else:
            device = torch.device("cpu")
    else:
        device = torch.device(device_str)

    logger.info("Using device: %s", device)
    if device.type == "cuda":
        logger.info(
            "  GPU: %s | VRAM: %.1f GB",
            torch.cuda.get_device_name(device),
            torch.cuda.get_device_properties(device).total_memory / 1e9,
        )
    return device


# ---------------------------------------------------------------------------
# Model inspection
# ---------------------------------------------------------------------------

def count_parameters(model: nn.Module, trainable_only: bool = True) -> int:
    """
    Count the number of (trainable) parameters in a model.

    Parameters
    ----------
    model : nn.Module
    trainable_only : bool
        If True, count only parameters with requires_grad=True.

    Returns
    -------
    int
    """
    if trainable_only:
        n = sum(p.numel() for p in model.parameters() if p.requires_grad)
    else:
        n = sum(p.numel() for p in model.parameters())
    logger.info(
        "Model parameters: %s%s.",
        f"{n:,}",
        " (trainable)" if trainable_only else " (total)",
    )
    return n


def save_model_info(
    model: nn.Module,
    path: Union[str, Path],
    extra: Optional[Dict] = None,
) -> None:
    """
    Persist a JSON summary of the model to *path*.

    The summary includes:
      - model class name
      - total and trainable parameter counts
      - layer names and shapes
      - any extra key-value pairs from *extra*

    Parameters
    ----------
    model : nn.Module
    path : str or Path
    extra : dict, optional
        Additional metadata to embed (e.g. class names, config).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    layers = []
    for name, module in model.named_modules():
        if len(list(module.children())) == 0:   # leaf modules only
            params = sum(p.numel() for p in module.parameters())
            layers.append({
                "name": name,
                "type": module.__class__.__name__,
                "parameters": params,
            })

    info: Dict = {
        "model_class": model.__class__.__name__,
        "total_parameters": count_parameters(model, trainable_only=False),
        "trainable_parameters": count_parameters(model, trainable_only=True),
        "layers": layers,
    }
    if extra:
        info.update(extra)

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(info, fh, indent=2)

    logger.info("Model info saved to '%s'.", path)


# ---------------------------------------------------------------------------
# Class weights
# ---------------------------------------------------------------------------

def load_class_weights(
    class_counts: Union[Dict[str, int], List[int]],
    device: Optional[torch.device] = None,
    smoothing: float = 0.0,
) -> torch.Tensor:
    """
    Compute inverse-frequency class weights for a weighted loss function.

    Parameters
    ----------
    class_counts : dict or list
        If dict: {class_name: count}.  Values are sorted by key.
        If list: [count_class0, count_class1, ...].
    device : torch.device, optional
        Move the weight tensor to this device.
    smoothing : float
        Add *smoothing* to each count to avoid division by zero for
        rare / unseen classes.

    Returns
    -------
    torch.Tensor  shape (num_classes,)
    """
    if isinstance(class_counts, dict):
        counts = [class_counts[k] + smoothing for k in sorted(class_counts)]
    else:
        counts = [c + smoothing for c in class_counts]

    counts_arr = np.array(counts, dtype=np.float64)
    total = counts_arr.sum()
    weights = total / (len(counts_arr) * counts_arr)   # inverse frequency
    weights = weights / weights.sum()                   # normalise to sum=1

    weight_tensor = torch.tensor(weights, dtype=torch.float32)
    if device is not None:
        weight_tensor = weight_tensor.to(device)

    logger.info(
        "Class weights: min=%.4f max=%.4f (n_classes=%d).",
        weight_tensor.min().item(), weight_tensor.max().item(), len(counts),
    )
    return weight_tensor


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------

def get_learning_rate(optimizer: torch.optim.Optimizer) -> float:
    """Return the current learning rate from the first param group."""
    return optimizer.param_groups[0]["lr"]


def cosine_warmup_lr(
    epoch: int,
    warmup_epochs: int,
    base_lr: float,
    min_lr: float = 1e-6,
) -> float:
    """
    Compute a cosine-annealing LR with a linear warm-up phase.

    Intended for use with ``torch.optim.lr_scheduler.LambdaLR``.

    Parameters
    ----------
    epoch : int
        Current epoch (0-indexed).
    warmup_epochs : int
        Number of warm-up epochs (linear ramp from min_lr to base_lr).
    base_lr : float
        Target LR after warm-up.
    min_lr : float
        Minimum LR at the end of cosine decay.

    Returns
    -------
    float  (scaling factor relative to base_lr)
    """
    if epoch < warmup_epochs:
        return max(min_lr, base_lr * (epoch + 1) / warmup_epochs) / base_lr
    progress = (epoch - warmup_epochs) / max(1, 100 - warmup_epochs)
    cosine_factor = 0.5 * (1.0 + np.cos(np.pi * progress))
    return max(min_lr, min_lr + (base_lr - min_lr) * cosine_factor) / base_lr


def format_time(seconds: float) -> str:
    """Convert seconds into a human-readable HH:MM:SS string."""
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h:02d}h {m:02d}m {s:02d}s"
    return f"{m:02d}m {s:02d}s"


def ensure_dir(path: Union[str, Path]) -> Path:
    """Create *path* and all parents if they don't exist. Return Path object."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
