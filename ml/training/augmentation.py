"""
ml/training/augmentation.py
----------------------------
Albumentations-based image augmentation pipelines.

Three pipelines:
  get_train_transforms  – heavy augmentation for training
  get_val_transforms    – resize + normalise only (validation)
  get_test_transforms   – resize + normalise only (test / inference)
"""

from __future__ import annotations

import logging
from typing import Tuple

import albumentations as A
from albumentations.pytorch import ToTensorV2

logger = logging.getLogger(__name__)

# ImageNet statistics (used as default when not overridden)
_IMAGENET_MEAN: Tuple[float, float, float] = (0.485, 0.456, 0.406)
_IMAGENET_STD: Tuple[float, float, float] = (0.229, 0.224, 0.225)


# ---------------------------------------------------------------------------
# Training pipeline
# ---------------------------------------------------------------------------

def get_train_transforms(
    image_size: Tuple[int, int] = (300, 300),
    mean: Tuple[float, float, float] = _IMAGENET_MEAN,
    std: Tuple[float, float, float] = _IMAGENET_STD,
    p_heavy: float = 0.5,
) -> A.Compose:
    """
    Return a heavy augmentation pipeline suitable for training.

    Transformations applied (in order):
      1.  RandomResizedCrop   – scale & aspect-ratio jitter
      2.  HorizontalFlip      – left-right mirror
      3.  VerticalFlip        – up-down mirror (rocks can be photographed any way)
      4.  RandomRotate90      – 90 ° rotations
      5.  ShiftScaleRotate    – arbitrary affine
      6.  ColorJitter         – brightness / contrast / saturation / hue
      7.  RandomBrightnessContrast
      8.  HueSaturationValue
      9.  CLAHE               – local contrast enhancement
      10. GaussianBlur        – lens / motion blur simulation
      11. MotionBlur
      12. GaussNoise          – sensor noise
      13. ISONoise
      14. ElasticTransform    – fine-grained texture deformation
      15. GridDistortion
      16. OpticalDistortion
      17. Cutout / CoarseDropout – occlusion
      18. RandomShadow        – lighting variation
      19. Normalize + ToTensorV2
    """
    h, w = image_size

    train_tfm = A.Compose([
        # ── Spatial ──────────────────────────────────────────────────────── #
        A.RandomResizedCrop(
            height=h, width=w,
            scale=(0.6, 1.0), ratio=(0.75, 1.33),
            p=1.0,
        ),
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.3),
        A.RandomRotate90(p=0.4),
        A.ShiftScaleRotate(
            shift_limit=0.1, scale_limit=0.2, rotate_limit=45,
            border_mode=0, p=p_heavy,
        ),

        # ── Photometric ──────────────────────────────────────────────────── #
        A.OneOf([
            A.ColorJitter(
                brightness=0.3, contrast=0.3,
                saturation=0.3, hue=0.1, p=1.0,
            ),
            A.RandomBrightnessContrast(
                brightness_limit=0.3, contrast_limit=0.3, p=1.0,
            ),
        ], p=0.7),

        A.HueSaturationValue(
            hue_shift_limit=20, sat_shift_limit=30, val_shift_limit=20, p=0.4,
        ),
        A.CLAHE(clip_limit=4.0, tile_grid_size=(8, 8), p=0.3),

        # ── Blur / noise ─────────────────────────────────────────────────── #
        A.OneOf([
            A.GaussianBlur(blur_limit=(3, 7), p=1.0),
            A.MotionBlur(blur_limit=7, p=1.0),
            A.MedianBlur(blur_limit=5, p=1.0),
        ], p=0.3),

        A.OneOf([
            A.GaussNoise(var_limit=(10.0, 50.0), p=1.0),
            A.ISONoise(color_shift=(0.01, 0.05), intensity=(0.1, 0.5), p=1.0),
        ], p=0.3),

        # ── Geometric distortions ────────────────────────────────────────── #
        A.OneOf([
            A.ElasticTransform(
                alpha=120, sigma=120 * 0.05, alpha_affine=120 * 0.03, p=1.0,
            ),
            A.GridDistortion(num_steps=5, distort_limit=0.3, p=1.0),
            A.OpticalDistortion(distort_limit=0.3, shift_limit=0.05, p=1.0),
        ], p=0.2),

        # ── Occlusion ────────────────────────────────────────────────────── #
        A.CoarseDropout(
            max_holes=8, max_height=h // 8, max_width=w // 8,
            min_holes=1, fill_value=0, p=0.3,
        ),

        # ── Lighting ─────────────────────────────────────────────────────── #
        A.RandomShadow(
            shadow_roi=(0, 0.5, 1, 1),
            num_shadows_lower=1, num_shadows_upper=2,
            shadow_dimension=5, p=0.2,
        ),

        # ── Finalise ─────────────────────────────────────────────────────── #
        A.Normalize(mean=mean, std=std, max_pixel_value=255.0),
        ToTensorV2(),
    ])

    logger.debug("Train transforms created (size=%s).", image_size)
    return train_tfm


# ---------------------------------------------------------------------------
# Validation pipeline
# ---------------------------------------------------------------------------

def get_val_transforms(
    image_size: Tuple[int, int] = (300, 300),
    mean: Tuple[float, float, float] = _IMAGENET_MEAN,
    std: Tuple[float, float, float] = _IMAGENET_STD,
) -> A.Compose:
    """
    Minimal deterministic pipeline for validation:
      Resize → Normalize → ToTensor
    """
    h, w = image_size

    val_tfm = A.Compose([
        A.Resize(height=h, width=w, interpolation=1),   # cv2.INTER_LINEAR
        A.Normalize(mean=mean, std=std, max_pixel_value=255.0),
        ToTensorV2(),
    ])

    logger.debug("Val transforms created (size=%s).", image_size)
    return val_tfm


# ---------------------------------------------------------------------------
# Test pipeline
# ---------------------------------------------------------------------------

def get_test_transforms(
    image_size: Tuple[int, int] = (300, 300),
    mean: Tuple[float, float, float] = _IMAGENET_MEAN,
    std: Tuple[float, float, float] = _IMAGENET_STD,
) -> A.Compose:
    """
    Identical to validation: deterministic resize + normalise.
    Kept as a separate function to allow test-time augmentation (TTA)
    to be inserted here in the future.
    """
    h, w = image_size

    test_tfm = A.Compose([
        A.Resize(height=h, width=w, interpolation=1),
        A.Normalize(mean=mean, std=std, max_pixel_value=255.0),
        ToTensorV2(),
    ])

    logger.debug("Test transforms created (size=%s).", image_size)
    return test_tfm


# ---------------------------------------------------------------------------
# TTA pipeline (Test-Time Augmentation)
# ---------------------------------------------------------------------------

def get_tta_transforms(
    image_size: Tuple[int, int] = (300, 300),
    mean: Tuple[float, float, float] = _IMAGENET_MEAN,
    std: Tuple[float, float, float] = _IMAGENET_STD,
) -> list:
    """
    Return a list of light augmentation pipelines for TTA.
    Average the softmax scores across all pipelines for the final prediction.
    """
    h, w = image_size
    base = [
        A.Resize(height=h, width=w),
        A.Normalize(mean=mean, std=std, max_pixel_value=255.0),
        ToTensorV2(),
    ]

    pipelines = [
        A.Compose(base),
        A.Compose([A.HorizontalFlip(p=1.0)] + base),
        A.Compose([A.VerticalFlip(p=1.0)] + base),
        A.Compose([A.Rotate(limit=10, p=1.0)] + base),
        A.Compose([A.RandomBrightnessContrast(p=1.0)] + base),
    ]

    logger.debug("TTA transforms created (size=%s, variants=%d).", image_size, len(pipelines))
    return pipelines
