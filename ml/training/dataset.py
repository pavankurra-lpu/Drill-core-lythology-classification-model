"""
ml/training/dataset.py
-----------------------
PyTorch Dataset and DataModule for the Lithology Classification System.

Supported directory layouts
---------------------------
Layout A – pre-split (recommended):
    root/
        train/
            Granite/  *.jpg …
            Basalt/   *.jpg …
            …
        val/
            Granite/  …
        test/
            Granite/  …

Layout B – flat class directories (auto-split):
    root/
        Granite/  *.jpg …
        Basalt/   *.jpg …
        …

Layout C – custom uploaded dataset (list of (path, label) pairs).
"""

from __future__ import annotations

import logging
import os
import random
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler

from ml.training.augmentation import (
    get_test_transforms,
    get_train_transforms,
    get_val_transforms,
)

logger = logging.getLogger(__name__)

# Supported image file extensions
_IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}


# ---------------------------------------------------------------------------
# Helper: discover image files
# ---------------------------------------------------------------------------

def _find_images(directory: Union[str, Path]) -> List[Tuple[Path, str]]:
    """
    Recursively discover images under *directory*.

    Returns
    -------
    List of (absolute_path, class_name) tuples, where class_name is the
    immediate parent directory of each image file.
    """
    directory = Path(directory)
    items: List[Tuple[Path, str]] = []

    for cls_dir in sorted(directory.iterdir()):
        if not cls_dir.is_dir():
            continue
        class_name = cls_dir.name
        for img_path in sorted(cls_dir.rglob("*")):
            if img_path.suffix.lower() in _IMG_EXTS and img_path.is_file():
                items.append((img_path, class_name))

    if not items:
        logger.warning("No images found in '%s'.", directory)
    else:
        logger.info("Discovered %d images across %d classes in '%s'.",
                    len(items), len({c for _, c in items}), directory)
    return items


def _load_image_cv2(path: Union[str, Path]) -> np.ndarray:
    """Load an image as a uint8 RGB ndarray via OpenCV."""
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise OSError(f"Cannot read image: {path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

class LithologyDataset(Dataset):
    """
    PyTorch Dataset for lithology image classification.

    Parameters
    ----------
    samples : List[Tuple[Path, str]]
        List of (image_path, class_name) pairs.
    class_to_idx : Dict[str, int]
        Mapping from class names to integer labels.
    transform : callable, optional
        Albumentations transform (applied to uint8 RGB ndarray).
    augment_synthetic : bool
        Future hook for synthetic data augmentation.
    """

    def __init__(
        self,
        samples: List[Tuple[Union[str, Path], str]],
        class_to_idx: Dict[str, int],
        transform: Optional[Callable] = None,
        augment_synthetic: bool = False,
    ) -> None:
        super().__init__()

        self.samples = [(Path(p), c) for p, c in samples]
        self.class_to_idx = class_to_idx
        self.idx_to_class = {v: k for k, v in class_to_idx.items()}
        self.transform = transform
        self.augment_synthetic = augment_synthetic

        # Validate all classes exist in mapping
        unknown = {c for _, c in self.samples if c not in class_to_idx}
        if unknown:
            raise ValueError(f"Unknown class(es) in dataset: {unknown}. "
                             f"Known: {list(class_to_idx.keys())}")

        logger.info("LithologyDataset | %d samples | %d classes",
                    len(self.samples), len(class_to_idx))

    # ---------------------------------------------------------------------- #

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        img_path, class_name = self.samples[idx]
        label = self.class_to_idx[class_name]

        # Load image
        try:
            image = _load_image_cv2(img_path)
        except Exception as exc:
            logger.warning("Failed to load '%s': %s — using blank image.", img_path, exc)
            # Return a blank image of a standard size
            image = np.zeros((300, 300, 3), dtype=np.uint8)

        # Apply augmentation / normalisation
        if self.transform is not None:
            transformed = self.transform(image=image)
            image = transformed["image"]   # torch.Tensor (C, H, W)
        else:
            image = torch.from_numpy(image.transpose(2, 0, 1)).float() / 255.0

        return image, label

    # ---------------------------------------------------------------------- #

    def get_class_counts(self) -> Dict[str, int]:
        """Return a dict mapping class_name → sample count."""
        counts: Dict[str, int] = {}
        for _, cls in self.samples:
            counts[cls] = counts.get(cls, 0) + 1
        return counts

    def get_sample_weights(self) -> List[float]:
        """
        Compute per-sample weights for WeightedRandomSampler.
        Inversely proportional to class frequency.
        """
        counts = self.get_class_counts()
        total = len(self.samples)
        class_weight = {cls: total / cnt for cls, cnt in counts.items()}
        return [class_weight[cls] for _, cls in self.samples]

    def get_labels(self) -> List[int]:
        """Return a list of integer labels for all samples."""
        return [self.class_to_idx[cls] for _, cls in self.samples]

    def __repr__(self) -> str:
        return (f"LithologyDataset(n_samples={len(self)}, "
                f"n_classes={len(self.class_to_idx)})")


# ---------------------------------------------------------------------------
# DataModule
# ---------------------------------------------------------------------------

class LithologyDataModule:
    """
    Manages train / val / test splits and returns DataLoaders.

    Supports three modes (auto-detected):
      A) `train_dir`, `val_dir`, `test_dir` are provided and exist.
      B) `data_dir` is provided (flat, no split subdirs) → random split.
      C) Custom lists of (path, label) tuples passed via `from_lists()`.

    Parameters
    ----------
    data_dir : str or Path, optional
        Root data directory (used in Mode A and B).
    train_dir : str or Path, optional
        Explicit training directory (Mode A).
    val_dir : str or Path, optional
        Explicit validation directory (Mode A).
    test_dir : str or Path, optional
        Explicit test directory (Mode A).
    class_names : List[str], optional
        Expected class names; inferred from directory if not given.
    image_size : Tuple[int, int]
        (H, W) to resize images to.
    batch_size : int
        Dataloader batch size.
    num_workers : int
        Dataloader worker count.
    pin_memory : bool
        Pin memory for faster GPU transfer.
    val_split : float
        Fraction of data for validation (Mode B only).
    test_split : float
        Fraction of data for test (Mode B only).
    seed : int
        Random seed for reproducible splits.
    use_weighted_sampler : bool
        Balance classes in training by sampling inversely proportional
        to class frequency.
    """

    def __init__(
        self,
        data_dir: Optional[Union[str, Path]] = None,
        train_dir: Optional[Union[str, Path]] = None,
        val_dir: Optional[Union[str, Path]] = None,
        test_dir: Optional[Union[str, Path]] = None,
        class_names: Optional[List[str]] = None,
        image_size: Tuple[int, int] = (300, 300),
        batch_size: int = 32,
        num_workers: int = 4,
        pin_memory: bool = True,
        val_split: float = 0.15,
        test_split: float = 0.15,
        seed: int = 42,
        use_weighted_sampler: bool = True,
        mean: Tuple[float, float, float] = (0.485, 0.456, 0.406),
        std: Tuple[float, float, float] = (0.229, 0.224, 0.225),
    ) -> None:
        self.data_dir = Path(data_dir) if data_dir else None
        self.train_dir = Path(train_dir) if train_dir else None
        self.val_dir = Path(val_dir) if val_dir else None
        self.test_dir = Path(test_dir) if test_dir else None
        self.class_names = class_names
        self.image_size = image_size
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.pin_memory = pin_memory
        self.val_split = val_split
        self.test_split = test_split
        self.seed = seed
        self.use_weighted_sampler = use_weighted_sampler
        self.mean = mean
        self.std = std

        self.class_to_idx: Dict[str, int] = {}
        self.idx_to_class: Dict[int, str] = {}

        self._train_ds: Optional[LithologyDataset] = None
        self._val_ds: Optional[LithologyDataset] = None
        self._test_ds: Optional[LithologyDataset] = None

        self._setup_done = False

    # ---------------------------------------------------------------------- #
    # Factory: custom list-based datasets                                      #
    # ---------------------------------------------------------------------- #

    @classmethod
    def from_lists(
        cls,
        train_samples: List[Tuple[Union[str, Path], str]],
        val_samples: List[Tuple[Union[str, Path], str]],
        test_samples: Optional[List[Tuple[Union[str, Path], str]]] = None,
        class_names: Optional[List[str]] = None,
        **kwargs,
    ) -> "LithologyDataModule":
        """
        Construct a DataModule from explicit sample lists.

        Parameters
        ----------
        train_samples, val_samples, test_samples :
            Each is a list of (image_path, class_name) tuples.
        class_names : list of str
            Ordered class names; inferred from samples if not given.
        **kwargs :
            Forwarded to ``__init__``.
        """
        dm = cls(**kwargs)

        # Derive class mapping
        all_classes = sorted({c for _, c in train_samples + val_samples +
                              (test_samples or [])})
        if class_names is not None:
            all_classes = class_names
        dm.class_to_idx = {c: i for i, c in enumerate(all_classes)}
        dm.idx_to_class = {i: c for c, i in dm.class_to_idx.items()}

        train_tfm = get_train_transforms(dm.image_size, dm.mean, dm.std)
        val_tfm = get_val_transforms(dm.image_size, dm.mean, dm.std)
        test_tfm = get_test_transforms(dm.image_size, dm.mean, dm.std)

        dm._train_ds = LithologyDataset(train_samples, dm.class_to_idx, train_tfm)
        dm._val_ds = LithologyDataset(val_samples, dm.class_to_idx, val_tfm)
        if test_samples:
            dm._test_ds = LithologyDataset(test_samples, dm.class_to_idx, test_tfm)
        dm._setup_done = True
        return dm

    # ---------------------------------------------------------------------- #
    # Setup                                                                    #
    # ---------------------------------------------------------------------- #

    def setup(self) -> None:
        """
        Discover images, build class mapping, and create dataset objects.
        Call this once before requesting DataLoaders.
        """
        if self._setup_done:
            return

        # Mode A: explicit train/val/test directories
        if self.train_dir and self.train_dir.exists():
            logger.info("DataModule Mode A: pre-split directories.")
            train_samples = _find_images(self.train_dir)
            val_samples = _find_images(self.val_dir) if (self.val_dir and self.val_dir.exists()) else []
            test_samples = _find_images(self.test_dir) if (self.test_dir and self.test_dir.exists()) else []

        # Mode B: flat directory → auto-split
        elif self.data_dir and self.data_dir.exists():
            logger.info("DataModule Mode B: flat directory, auto-split.")
            all_samples = _find_images(self.data_dir)
            train_samples, val_samples, test_samples = self._split(all_samples)

        else:
            raise FileNotFoundError(
                "Cannot locate data. Provide either 'train_dir' (Mode A) "
                "or 'data_dir' (Mode B)."
            )

        # Build class mapping
        all_classes = sorted({c for _, c in train_samples + val_samples + test_samples})
        if self.class_names is not None:
            all_classes = self.class_names
        self.class_to_idx = {c: i for i, c in enumerate(all_classes)}
        self.idx_to_class = {i: c for c, i in self.class_to_idx.items()}

        # Build transforms
        train_tfm = get_train_transforms(self.image_size, self.mean, self.std)
        val_tfm = get_val_transforms(self.image_size, self.mean, self.std)
        test_tfm = get_test_transforms(self.image_size, self.mean, self.std)

        # Build datasets
        self._train_ds = LithologyDataset(train_samples, self.class_to_idx, train_tfm)
        self._val_ds = LithologyDataset(val_samples, self.class_to_idx, val_tfm)
        if test_samples:
            self._test_ds = LithologyDataset(test_samples, self.class_to_idx, test_tfm)

        self._setup_done = True
        logger.info(
            "Setup complete | train=%d val=%d test=%d classes=%d",
            len(self._train_ds),
            len(self._val_ds) if self._val_ds else 0,
            len(self._test_ds) if self._test_ds else 0,
            len(self.class_to_idx),
        )

    def _split(
        self,
        samples: List[Tuple[Path, str]],
    ) -> Tuple[List, List, List]:
        """Stratified random split into train / val / test."""
        rng = random.Random(self.seed)

        # Group by class
        class_to_samples: Dict[str, List] = {}
        for item in samples:
            cls = item[1]
            class_to_samples.setdefault(cls, []).append(item)

        train, val, test = [], [], []
        for cls_samples in class_to_samples.values():
            rng.shuffle(cls_samples)
            n = len(cls_samples)
            n_test = max(1, int(n * self.test_split))
            n_val = max(1, int(n * self.val_split))
            n_train = n - n_val - n_test
            train.extend(cls_samples[:n_train])
            val.extend(cls_samples[n_train: n_train + n_val])
            test.extend(cls_samples[n_train + n_val:])

        logger.info("Split: train=%d val=%d test=%d", len(train), len(val), len(test))
        return train, val, test

    # ---------------------------------------------------------------------- #
    # DataLoaders                                                              #
    # ---------------------------------------------------------------------- #

    def train_dataloader(self) -> DataLoader:
        self._assert_setup()
        sampler = None
        shuffle = True
        if self.use_weighted_sampler:
            weights = self._train_ds.get_sample_weights()  # type: ignore[union-attr]
            sampler = WeightedRandomSampler(
                weights=weights,
                num_samples=len(weights),
                replacement=True,
            )
            shuffle = False   # sampler and shuffle are mutually exclusive
        return DataLoader(
            self._train_ds,             # type: ignore[arg-type]
            batch_size=self.batch_size,
            shuffle=shuffle,
            sampler=sampler,
            num_workers=self.num_workers,
            pin_memory=self.pin_memory,
            drop_last=True,
            persistent_workers=self.num_workers > 0,
        )

    def val_dataloader(self) -> DataLoader:
        self._assert_setup()
        return DataLoader(
            self._val_ds,               # type: ignore[arg-type]
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            pin_memory=self.pin_memory,
            drop_last=False,
            persistent_workers=self.num_workers > 0,
        )

    def test_dataloader(self) -> Optional[DataLoader]:
        self._assert_setup()
        if self._test_ds is None:
            logger.warning("No test dataset available.")
            return None
        return DataLoader(
            self._test_ds,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            pin_memory=self.pin_memory,
            drop_last=False,
            persistent_workers=self.num_workers > 0,
        )

    # ---------------------------------------------------------------------- #
    # Properties                                                               #
    # ---------------------------------------------------------------------- #

    @property
    def train_dataset(self) -> Optional[LithologyDataset]:
        return self._train_ds

    @property
    def val_dataset(self) -> Optional[LithologyDataset]:
        return self._val_ds

    @property
    def test_dataset(self) -> Optional[LithologyDataset]:
        return self._test_ds

    @property
    def num_classes(self) -> int:
        return len(self.class_to_idx)

    def _assert_setup(self) -> None:
        if not self._setup_done:
            raise RuntimeError("Call DataModule.setup() before requesting DataLoaders.")

    def __repr__(self) -> str:
        return (
            f"LithologyDataModule("
            f"train={len(self._train_ds) if self._train_ds else 0}, "
            f"val={len(self._val_ds) if self._val_ds else 0}, "
            f"test={len(self._test_ds) if self._test_ds else 0}, "
            f"classes={self.num_classes})"
        )
