"""
ml/config.py
------------
Central configuration for the Automated Lithology Classification System.
All hyper-parameters, class names, and path defaults live here.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple


# ---------------------------------------------------------------------------
# Rock / mineral taxonomy
# ---------------------------------------------------------------------------

LITHOLOGY_CLASSES: List[str] = [
    "Granite",
    "Basalt",
    "Sandstone",
    "Limestone",
    "Shale",
    "Quartzite",
    "Marble",
    "Slate",
    "Gneiss",
    "Diorite",
    "Gabbro",
    "Rhyolite",
    "Andesite",
    "Obsidian",
    "Pumice",
]

MINERAL_CLASSES: List[str] = [
    "Quartz",
    "Feldspar",
    "Mica",
    "Calcite",
    "Dolomite",
    "Pyrite",
    "Magnetite",
    "Olivine",
    "Pyroxene",
    "Amphibole",
    "Chlorite",
    "Serpentine",
]

# Mapping rock → likely minerals (used for mock predictions / UI hints)
LITHOLOGY_MINERAL_MAP: dict = {
    "Granite":    ["Quartz", "Feldspar", "Mica"],
    "Basalt":     ["Pyroxene", "Olivine", "Magnetite"],
    "Sandstone":  ["Quartz", "Feldspar"],
    "Limestone":  ["Calcite", "Dolomite"],
    "Shale":      ["Mica", "Quartz", "Chlorite"],
    "Quartzite":  ["Quartz"],
    "Marble":     ["Calcite", "Dolomite"],
    "Slate":      ["Mica", "Quartz", "Chlorite"],
    "Gneiss":     ["Quartz", "Feldspar", "Mica"],
    "Diorite":    ["Feldspar", "Amphibole", "Pyroxene"],
    "Gabbro":     ["Pyroxene", "Olivine", "Feldspar"],
    "Rhyolite":   ["Quartz", "Feldspar"],
    "Andesite":   ["Feldspar", "Pyroxene", "Amphibole"],
    "Obsidian":   ["Quartz", "Feldspar"],
    "Pumice":     ["Quartz", "Feldspar"],
}


# ---------------------------------------------------------------------------
# Data configuration
# ---------------------------------------------------------------------------

@dataclass
class DataConfig:
    """Dataset and data-loading settings."""

    dataset_root: str = "data"
    train_dir: str = "data/train"
    val_dir: str = "data/val"
    test_dir: str = "data/test"

    image_size: Tuple[int, int] = (300, 300)          # EfficientNet-B3 native
    image_channels: int = 3

    # DataLoader
    batch_size: int = 32
    num_workers: int = min(4, os.cpu_count() or 1)
    pin_memory: bool = True
    drop_last: bool = True

    # Splitting (used when a flat directory is given)
    train_split: float = 0.70
    val_split: float = 0.15
    test_split: float = 0.15

    # Normalisation (ImageNet stats)
    mean: Tuple[float, float, float] = (0.485, 0.456, 0.406)
    std: Tuple[float, float, float] = (0.229, 0.224, 0.225)

    # Supported image extensions
    valid_extensions: Tuple[str, ...] = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif")


# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------

@dataclass
class ModelConfig:
    """Architecture / model settings."""

    model_name: str = "efficientnet_b3"   # or "resnet50"
    num_classes: int = len(LITHOLOGY_CLASSES)
    pretrained: bool = True
    dropout_rate: float = 0.4

    # Checkpoints
    checkpoint_dir: str = "checkpoints"
    best_model_filename: str = "best_model.pth"
    last_model_filename: str = "last_model.pth"


# ---------------------------------------------------------------------------
# Training configuration
# ---------------------------------------------------------------------------

@dataclass
class TrainingConfig:
    """Training hyper-parameters."""

    # Optimiser
    learning_rate: float = 1e-4
    weight_decay: float = 1e-5
    optimizer: str = "adamw"           # "adam" | "adamw" | "sgd"
    momentum: float = 0.9              # used only when optimizer == "sgd"

    # Scheduler
    scheduler: str = "cosine"          # "cosine" | "step" | "plateau" | "none"
    step_size: int = 10                # StepLR
    gamma: float = 0.1                 # StepLR / ExponentialLR
    T_max: int = 50                    # CosineAnnealingLR
    patience_lr: int = 5               # ReduceLROnPlateau patience

    # Loop
    num_epochs: int = 50
    warmup_epochs: int = 3
    grad_clip: float = 1.0             # gradient clipping max-norm (0 = disabled)

    # Early stopping
    early_stopping_patience: int = 10
    early_stopping_min_delta: float = 1e-4
    monitor: str = "val_loss"          # "val_loss" | "val_acc"

    # Logging / checkpointing
    log_interval: int = 10             # steps between console logs
    tensorboard_dir: str = "runs"
    seed: int = 42

    # Mixed precision
    use_amp: bool = True               # Automatic Mixed Precision


# ---------------------------------------------------------------------------
# Inference configuration
# ---------------------------------------------------------------------------

@dataclass
class InferenceConfig:
    """Inference / serving settings."""

    model_path: str = "checkpoints/best_model.pth"
    model_name: str = "efficientnet_b3"
    device: str = "auto"               # "auto" | "cpu" | "cuda" | "mps"
    top_k: int = 5
    confidence_threshold: float = 0.10
    batch_size: int = 16
    gradcam_layer: str = "features.6"  # EfficientNet-B3 target layer


# ---------------------------------------------------------------------------
# Master config (composed)
# ---------------------------------------------------------------------------

@dataclass
class LithologyConfig:
    """Top-level config object that composes all sub-configs."""

    data: DataConfig = field(default_factory=DataConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    inference: InferenceConfig = field(default_factory=InferenceConfig)

    lithology_classes: List[str] = field(default_factory=lambda: LITHOLOGY_CLASSES)
    mineral_classes: List[str] = field(default_factory=lambda: MINERAL_CLASSES)
    lithology_mineral_map: dict = field(default_factory=lambda: LITHOLOGY_MINERAL_MAP)

    def __post_init__(self) -> None:
        """Ensure derived fields stay in sync."""
        self.model.num_classes = len(self.lithology_classes)
        # Create required directories
        for d in [
            self.data.dataset_root,
            self.data.train_dir,
            self.data.val_dir,
            self.data.test_dir,
            self.model.checkpoint_dir,
            self.training.tensorboard_dir,
        ]:
            Path(d).mkdir(parents=True, exist_ok=True)

    @property
    def num_classes(self) -> int:
        return len(self.lithology_classes)

    @property
    def num_mineral_classes(self) -> int:
        return len(self.mineral_classes)

    def to_dict(self) -> dict:
        """Serialise config to a plain dict (for logging / JSON export)."""
        import dataclasses
        return dataclasses.asdict(self)


# ---------------------------------------------------------------------------
# Convenience: module-level defaults
# ---------------------------------------------------------------------------

NUM_CLASSES: int = len(LITHOLOGY_CLASSES)
NUM_MINERAL_CLASSES: int = len(MINERAL_CLASSES)
IMAGE_SIZE: Tuple[int, int] = (300, 300)
BATCH_SIZE: int = 32
LEARNING_RATE: float = 1e-4
NUM_EPOCHS: int = 50
SEED: int = 42

# ImageNet normalisation
IMAGENET_MEAN: Tuple[float, float, float] = (0.485, 0.456, 0.406)
IMAGENET_STD: Tuple[float, float, float] = (0.229, 0.224, 0.225)

# Default config singleton (import and use directly in scripts)
DEFAULT_CONFIG = LithologyConfig()
