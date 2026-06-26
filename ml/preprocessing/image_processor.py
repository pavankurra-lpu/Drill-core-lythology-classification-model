"""
ml/preprocessing/image_processor.py
-------------------------------------
Image validation, loading, preprocessing, and feature extraction utilities.

ImageProcessor is stateless — all methods are either classmethods or
take explicit arguments, so the same instance can be reused across threads.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Supported file extensions
_VALID_EXTENSIONS: Tuple[str, ...] = (
    ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp",
)

# ImageNet normalisation constants
_IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


# ---------------------------------------------------------------------------
# ImageProcessor
# ---------------------------------------------------------------------------

class ImageProcessor:
    """
    Utility class for image loading, validation, preprocessing, and
    feature extraction for the lithology pipeline.

    All methods are designed to be called on raw uint8 RGB numpy arrays
    (H, W, 3) unless otherwise noted.
    """

    # ── Validation ────────────────────────────────────────────────────────── #

    @staticmethod
    def validate_image(file_path: Union[str, Path]) -> bool:
        """
        Check that a file exists, has a valid extension, and can be decoded.

        Parameters
        ----------
        file_path : str or Path

        Returns
        -------
        bool  True if valid, False otherwise (logs warning on failure).
        """
        path = Path(file_path)

        if not path.exists():
            logger.warning("validate_image: file not found — '%s'.", path)
            return False

        if path.suffix.lower() not in _VALID_EXTENSIONS:
            logger.warning(
                "validate_image: unsupported extension '%s' for '%s'.",
                path.suffix, path,
            )
            return False

        try:
            img = cv2.imread(str(path), cv2.IMREAD_COLOR)
            if img is None or img.size == 0:
                logger.warning("validate_image: cannot decode '%s'.", path)
                return False
        except Exception as exc:
            logger.warning("validate_image: exception for '%s': %s.", path, exc)
            return False

        return True

    # ── Loading ───────────────────────────────────────────────────────────── #

    @staticmethod
    def load_image(
        file_path_or_bytes: Union[str, Path, bytes],
        target_mode: str = "RGB",
    ) -> np.ndarray:
        """
        Load an image from a file path or raw bytes.

        Parameters
        ----------
        file_path_or_bytes : str, Path, or bytes
            File path or raw image bytes (e.g. from an HTTP upload).
        target_mode : str
            'RGB' or 'BGR' (OpenCV native).

        Returns
        -------
        np.ndarray  uint8  shape (H, W, 3)
        """
        if isinstance(file_path_or_bytes, (str, Path)):
            img = cv2.imread(str(file_path_or_bytes), cv2.IMREAD_COLOR)
            if img is None:
                raise OSError(f"Cannot read image: {file_path_or_bytes}")
        elif isinstance(file_path_or_bytes, bytes):
            arr = np.frombuffer(file_path_or_bytes, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("Cannot decode image from bytes.")
        else:
            raise TypeError(
                f"Expected str, Path, or bytes; got {type(file_path_or_bytes)}."
            )

        if target_mode == "RGB":
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return img

    # ── Resize ────────────────────────────────────────────────────────────── #

    @staticmethod
    def resize_image(
        image: np.ndarray,
        size: Tuple[int, int] = (300, 300),
        interpolation: int = cv2.INTER_LINEAR,
    ) -> np.ndarray:
        """
        Resize to (height, width).

        Parameters
        ----------
        image : np.ndarray  uint8  (H, W, 3)
        size : (height, width)
        interpolation : OpenCV interpolation flag

        Returns
        -------
        np.ndarray  uint8  (size[0], size[1], 3)
        """
        h, w = size
        return cv2.resize(image, (w, h), interpolation=interpolation)

    # ── Normalisation ─────────────────────────────────────────────────────── #

    @staticmethod
    def normalize_image(
        image: np.ndarray,
        mean: np.ndarray = _IMAGENET_MEAN,
        std: np.ndarray = _IMAGENET_STD,
    ) -> np.ndarray:
        """
        Normalise a uint8 or float32 image to float32 with given mean/std.

        Parameters
        ----------
        image : np.ndarray  (H, W, 3)  uint8 [0, 255] or float32 [0, 1]

        Returns
        -------
        np.ndarray  float32  (H, W, 3)
        """
        img = image.astype(np.float32)
        if img.max() > 1.0:
            img /= 255.0
        img = (img - mean) / std
        return img

    # ── Background removal ────────────────────────────────────────────────── #

    @staticmethod
    def remove_background(image: np.ndarray) -> np.ndarray:
        """
        Attempt to isolate the rock sample from a uniform background
        using GrabCut.  Falls back to the original image if the
        foreground mask is trivially small.

        Parameters
        ----------
        image : np.ndarray  uint8  RGB  (H, W, 3)

        Returns
        -------
        np.ndarray  uint8  RGB  (H, W, 3)  background pixels set to 0.
        """
        bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        mask = np.zeros(bgr.shape[:2], np.uint8)

        # Bounding rect = inner 80 % of the image
        h, w = bgr.shape[:2]
        margin_h, margin_w = int(h * 0.1), int(w * 0.1)
        rect = (margin_w, margin_h, w - 2 * margin_w, h - 2 * margin_h)

        try:
            bgd_model = np.zeros((1, 65), np.float64)
            fgd_model = np.zeros((1, 65), np.float64)
            cv2.grabCut(bgr, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
            fg_mask = np.where((mask == 2) | (mask == 0), 0, 1).astype(np.uint8)

            if fg_mask.sum() < 0.05 * h * w:
                logger.debug("remove_background: foreground too small, skipping.")
                return image

            result = image.copy()
            result[fg_mask == 0] = 0
            return result

        except cv2.error as exc:
            logger.warning("remove_background failed: %s. Returning original.", exc)
            return image

    # ── Contrast enhancement ──────────────────────────────────────────────── #

    @staticmethod
    def enhance_contrast(
        image: np.ndarray,
        method: str = "clahe",
        clip_limit: float = 2.0,
        tile_grid_size: Tuple[int, int] = (8, 8),
    ) -> np.ndarray:
        """
        Enhance image contrast.

        Parameters
        ----------
        image : np.ndarray  uint8  RGB  (H, W, 3)
        method : 'clahe' | 'histogram_eq' | 'gamma'
        clip_limit : CLAHE clip limit.
        tile_grid_size : CLAHE tile grid size.

        Returns
        -------
        np.ndarray  uint8  RGB  (H, W, 3)
        """
        if method == "clahe":
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
            l_channel, a_channel, b_channel = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
            l_enhanced = clahe.apply(l_channel)
            lab_enhanced = cv2.merge([l_enhanced, a_channel, b_channel])
            return cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2RGB)

        elif method == "histogram_eq":
            yuv = cv2.cvtColor(image, cv2.COLOR_RGB2YUV)
            yuv[:, :, 0] = cv2.equalizeHist(yuv[:, :, 0])
            return cv2.cvtColor(yuv, cv2.COLOR_YUV2RGB)

        elif method == "gamma":
            gamma = clip_limit   # reuse parameter
            inv_gamma = 1.0 / gamma
            table = np.array(
                [((i / 255.0) ** inv_gamma) * 255 for i in range(256)], dtype=np.uint8
            )
            return cv2.LUT(image, table)

        else:
            raise ValueError(f"Unknown contrast method: '{method}'.")

    # ── Colour features ───────────────────────────────────────────────────── #

    @staticmethod
    def extract_color_features(image: np.ndarray) -> Dict[str, Any]:
        """
        Extract colour-space statistics from an image.

        Extracts features in RGB, HSV, and LAB colour spaces.

        Parameters
        ----------
        image : np.ndarray  uint8  RGB  (H, W, 3)

        Returns
        -------
        dict with keys:
            rgb_mean, rgb_std,
            hsv_mean, hsv_std,
            lab_mean, lab_std,
            dominant_colors (list of [R, G, B] for 5 clusters),
            color_entropy.
        """
        # ── RGB stats ───────────────────────────────────────────────────── #
        rgb_mean = image.mean(axis=(0, 1)).tolist()
        rgb_std = image.std(axis=(0, 1)).tolist()

        # ── HSV stats ───────────────────────────────────────────────────── #
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        hsv_mean = hsv.mean(axis=(0, 1)).tolist()
        hsv_std = hsv.std(axis=(0, 1)).tolist()

        # ── LAB stats ───────────────────────────────────────────────────── #
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        lab_mean = lab.mean(axis=(0, 1)).tolist()
        lab_std = lab.std(axis=(0, 1)).tolist()

        # ── Dominant colours (k-means) ───────────────────────────────────── #
        try:
            pixels = image.reshape(-1, 3).astype(np.float32)
            n_clusters = min(5, len(pixels))
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
            _, _, centers = cv2.kmeans(
                pixels, n_clusters, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS
            )
            dominant_colors = centers.astype(int).tolist()
        except cv2.error:
            dominant_colors = []

        # ── Colour entropy ───────────────────────────────────────────────── #
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
        hist_norm = hist / (hist.sum() + 1e-10)
        entropy = float(-np.sum(hist_norm * np.log2(hist_norm + 1e-10)))

        return {
            "rgb_mean": rgb_mean,
            "rgb_std": rgb_std,
            "hsv_mean": hsv_mean,
            "hsv_std": hsv_std,
            "lab_mean": lab_mean,
            "lab_std": lab_std,
            "dominant_colors": dominant_colors,
            "color_entropy": entropy,
        }

    # ── Texture features ──────────────────────────────────────────────────── #

    @staticmethod
    def extract_texture_features(image: np.ndarray) -> Dict[str, Any]:
        """
        Extract texture descriptors from an image.

        Includes: Laplacian variance (sharpness), GLCM-like edge density,
        Gabor filter responses, and Local Binary Pattern histogram.

        Parameters
        ----------
        image : np.ndarray  uint8  RGB  (H, W, 3)

        Returns
        -------
        dict with keys:
            sharpness, edge_density, gradient_mean, gradient_std,
            gabor_responses (list of 4 floats), lbp_hist (list of 10 floats).
        """
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        # ── Sharpness (Laplacian variance) ───────────────────────────────── #
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = float(laplacian.var())

        # ── Edge density ─────────────────────────────────────────────────── #
        edges = cv2.Canny(gray, 50, 150)
        edge_density = float(edges.mean())

        # ── Gradient statistics ───────────────────────────────────────────── #
        gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_mag = np.sqrt(gx ** 2 + gy ** 2)
        gradient_mean = float(gradient_mag.mean())
        gradient_std = float(gradient_mag.std())

        # ── Gabor filter responses ────────────────────────────────────────── #
        gabor_responses: List[float] = []
        gray_f = gray.astype(np.float32)
        for theta in [0, np.pi / 4, np.pi / 2, 3 * np.pi / 4]:
            kernel = cv2.getGaborKernel(
                ksize=(21, 21), sigma=5.0, theta=theta,
                lambd=10.0, gamma=0.5, psi=0,
            )
            filtered = cv2.filter2D(gray_f, cv2.CV_32F, kernel)
            gabor_responses.append(float(filtered.mean()))

        # ── LBP histogram (simplified) ────────────────────────────────────── #
        # Use a coarse histogram of grey values as a proxy for LBP
        hist = cv2.calcHist([gray], [0], None, [10], [0, 256]).flatten()
        hist_norm = (hist / (hist.sum() + 1e-10)).tolist()

        return {
            "sharpness": sharpness,
            "edge_density": edge_density,
            "gradient_mean": gradient_mean,
            "gradient_std": gradient_std,
            "gabor_responses": gabor_responses,
            "lbp_hist": hist_norm,
        }

    # ── Full preprocessing info ───────────────────────────────────────────── #

    @classmethod
    def get_preprocessing_info(
        cls,
        image_path: Union[str, Path],
    ) -> Dict[str, Any]:
        """
        Load an image and return a comprehensive stats / feature dictionary.

        Parameters
        ----------
        image_path : str or Path

        Returns
        -------
        dict with keys:
            valid, path, format, shape, dtype, file_size_kb,
            min_pixel, max_pixel, mean_pixel, std_pixel,
            is_grayscale, aspect_ratio,
            color_features (from extract_color_features),
            texture_features (from extract_texture_features).
        """
        path = Path(image_path)

        info: Dict[str, Any] = {
            "valid": False,
            "path": str(path),
            "format": path.suffix.lower(),
        }

        # Validation
        if not cls.validate_image(path):
            return info

        try:
            image = cls.load_image(path, target_mode="RGB")
        except Exception as exc:
            logger.warning("get_preprocessing_info: load failed: %s.", exc)
            return info

        h, w, c = image.shape
        file_size_kb = path.stat().st_size / 1024

        info.update({
            "valid": True,
            "shape": (h, w, c),
            "dtype": str(image.dtype),
            "file_size_kb": round(file_size_kb, 2),
            "min_pixel": int(image.min()),
            "max_pixel": int(image.max()),
            "mean_pixel": round(float(image.mean()), 2),
            "std_pixel": round(float(image.std()), 2),
            "is_grayscale": bool(
                np.allclose(image[:, :, 0], image[:, :, 1]) and
                np.allclose(image[:, :, 1], image[:, :, 2])
            ),
            "aspect_ratio": round(w / h, 3),
            "color_features": cls.extract_color_features(image),
            "texture_features": cls.extract_texture_features(image),
        })

        return info
