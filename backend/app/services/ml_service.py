"""
MLService — loads PyTorch models and runs lithology classification inference.
Falls back to deterministic mock predictions when model weights are unavailable,
so the application works without a GPU or pre-trained weights.
"""
from __future__ import annotations

import hashlib
import logging
import os
import random
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Lithology taxonomy ────────────────────────────────────────────────────────
LITHOLOGY_CLASSES = [
    "Sandstone",
    "Limestone",
    "Shale",
    "Granite",
    "Basalt",
    "Quartzite",
    "Dolomite",
    "Mudstone",
    "Conglomerate",
    "Andesite",
]

ROCK_TYPE_MAP: Dict[str, str] = {
    "Sandstone": "Sedimentary",
    "Limestone": "Sedimentary",
    "Shale": "Sedimentary",
    "Dolomite": "Sedimentary",
    "Mudstone": "Sedimentary",
    "Conglomerate": "Sedimentary",
    "Granite": "Igneous",
    "Basalt": "Igneous",
    "Andesite": "Igneous",
    "Quartzite": "Metamorphic",
}

MINERAL_ASSOCIATIONS: Dict[str, Dict[str, float]] = {
    "Sandstone": {"Quartz": 0.65, "Feldspar": 0.15, "Clay": 0.12, "Iron Oxide": 0.08},
    "Limestone": {"Calcite": 0.75, "Dolomite": 0.10, "Clay": 0.08, "Quartz": 0.07},
    "Shale": {"Clay": 0.55, "Quartz": 0.25, "Feldspar": 0.10, "Organic": 0.10},
    "Granite": {"Quartz": 0.30, "Feldspar": 0.40, "Mica": 0.20, "Hornblende": 0.10},
    "Basalt": {"Pyroxene": 0.40, "Plagioclase": 0.35, "Olivine": 0.15, "Iron Oxide": 0.10},
    "Quartzite": {"Quartz": 0.90, "Feldspar": 0.05, "Mica": 0.05},
    "Dolomite": {"Dolomite": 0.80, "Calcite": 0.10, "Clay": 0.10},
    "Mudstone": {"Clay": 0.60, "Quartz": 0.25, "Feldspar": 0.10, "Carbonate": 0.05},
    "Conglomerate": {"Quartz": 0.45, "Feldspar": 0.25, "Rock Fragments": 0.20, "Clay": 0.10},
    "Andesite": {"Plagioclase": 0.50, "Pyroxene": 0.25, "Hornblende": 0.15, "Iron Oxide": 0.10},
}


class MLService:
    """
    Service class for loading ML models and running lithology classification.

    The service attempts to load PyTorch model weights from disk.
    If unavailable, it uses a seeded mock predictor that returns
    deterministic, realistic-looking outputs based on image content hash.
    """

    def __init__(self) -> None:
        self._models: Dict[str, Any] = {}
        self._transform: Optional[Any] = None
        self._torch_available = False
        self._try_import_torch()

    def _try_import_torch(self) -> None:
        try:
            import torch  # noqa: F401, PLC0415
            import torchvision  # noqa: F401, PLC0415

            self._torch_available = True
            logger.info("PyTorch is available (torch=%s)", torch.__version__)
        except ImportError:
            logger.warning("PyTorch not installed — using mock predictor")

    def _build_transform(self) -> Any:
        """Build a torchvision preprocessing transform pipeline."""
        from torchvision import transforms  # noqa: PLC0415

        return transforms.Compose([
            transforms.Resize((settings.IMAGE_SIZE, settings.IMAGE_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])

    def load_model(self, model_name: str) -> Optional[Any]:
        """
        Load a model from disk if not already cached.

        Returns:
            PyTorch model in eval mode, or None if weights not available.
        """
        if model_name in self._models:
            return self._models[model_name]

        if not self._torch_available:
            return None

        weights_map = {
            "efficientnet": settings.EFFICIENTNET_WEIGHTS,
            "resnet50": settings.RESNET_WEIGHTS,
            "mobilenet": settings.MOBILENET_WEIGHTS,
        }
        weights_path = weights_map.get(model_name)

        if not weights_path or not os.path.exists(weights_path):
            logger.warning(
                "Weights not found for model '%s' at '%s' — using mock predictor",
                model_name, weights_path,
            )
            return None

        try:
            import torch  # noqa: PLC0415
            import torchvision.models as tv_models  # noqa: PLC0415

            num_classes = settings.NUM_CLASSES

            if model_name == "efficientnet":
                model = tv_models.efficientnet_b3(weights=None)
                model.classifier[1] = torch.nn.Linear(
                    model.classifier[1].in_features, num_classes
                )
            elif model_name == "resnet50":
                model = tv_models.resnet50(weights=None)
                model.fc = torch.nn.Linear(model.fc.in_features, num_classes)
            elif model_name == "mobilenet":
                model = tv_models.mobilenet_v3_large(weights=None)
                model.classifier[3] = torch.nn.Linear(
                    model.classifier[3].in_features, num_classes
                )
            else:
                logger.error("Unknown model architecture: %s", model_name)
                return None

            state_dict = torch.load(weights_path, map_location="cpu")
            model.load_state_dict(state_dict)
            model.eval()

            self._models[model_name] = model
            if self._transform is None:
                self._transform = self._build_transform()

            logger.info("Model '%s' loaded from %s", model_name, weights_path)
            return model

        except Exception as exc:
            logger.error("Failed to load model '%s': %s", model_name, exc)
            return None

    def preprocess_image(self, image_path: str) -> Any:
        """
        Load and preprocess an image for inference.

        Returns:
            A normalised torch.Tensor of shape [1, 3, H, W], or None on failure.
        """
        if not self._torch_available:
            return None
        try:
            from PIL import Image  # noqa: PLC0415
            import torch  # noqa: PLC0415

            if self._transform is None:
                self._transform = self._build_transform()

            img = Image.open(image_path).convert("RGB")
            tensor = self._transform(img).unsqueeze(0)  # type: ignore[operator]
            logger.debug("Image preprocessed: shape=%s", tensor.shape)
            return tensor
        except Exception as exc:
            logger.error("Image preprocessing failed for %s: %s", image_path, exc)
            return None

    def _mock_predict(self, image_path: str, model_name: str) -> Dict[str, Any]:
        """
        Generate deterministic mock predictions seeded by the image file hash.
        Produces realistic-looking outputs for development/testing.
        """
        # Seed RNG from file content hash for reproducibility
        try:
            with open(image_path, "rb") as f:
                content = f.read(4096)
            seed = int(hashlib.md5(content).hexdigest(), 16) % (2 ** 32)
        except Exception:
            seed = 42

        rng = random.Random(seed)
        class_idx = rng.randint(0, len(LITHOLOGY_CLASSES) - 1)
        lithology = LITHOLOGY_CLASSES[class_idx]

        # Build softmax-like score distribution
        raw_scores = [rng.uniform(0.01, 0.15) for _ in LITHOLOGY_CLASSES]
        raw_scores[class_idx] = rng.uniform(0.55, 0.95)
        total = sum(raw_scores)
        probabilities = [s / total for s in raw_scores]

        confidence = probabilities[class_idx]
        top_predictions = sorted(
            [
                {"class": cls, "confidence": round(prob, 4)}
                for cls, prob in zip(LITHOLOGY_CLASSES, probabilities)
            ],
            key=lambda x: x["confidence"],
            reverse=True,
        )[:5]

        minerals = MINERAL_ASSOCIATIONS.get(lithology, {})
        mineral_preds = {
            mineral: round(pct + rng.uniform(-0.03, 0.03), 4)
            for mineral, pct in minerals.items()
        }

        return {
            "rock_type": ROCK_TYPE_MAP.get(lithology, "Unknown"),
            "lithology_class": lithology,
            "mineral_predictions": mineral_preds,
            "confidence_score": round(confidence, 4),
            "top_predictions": top_predictions,
            "model_used": model_name,
            "mock": True,
        }

    def predict(self, image_path: str, model_name: str = "efficientnet") -> Dict[str, Any]:
        """
        Run lithology classification on the given image.

        Tries real PyTorch inference first; falls back to mock predictor.

        Args:
            image_path: Absolute path to the image file.
            model_name: Which model architecture to use.

        Returns:
            Dict with rock_type, lithology_class, mineral_predictions,
            confidence_score, top_predictions, preprocessing_info, model_used,
            processing_time.
        """
        start_time = time.perf_counter()
        preprocessing_info: Dict[str, Any] = {}

        model = self.load_model(model_name)

        if model is not None and self._torch_available:
            try:
                import torch  # noqa: PLC0415
                from PIL import Image  # noqa: PLC0415

                img = Image.open(image_path).convert("RGB")
                w, h = img.size
                preprocessing_info = {
                    "original_size": [w, h],
                    "target_size": [settings.IMAGE_SIZE, settings.IMAGE_SIZE],
                    "normalised": True,
                    "mode": "RGB",
                }

                tensor = self.preprocess_image(image_path)
                if tensor is None:
                    raise RuntimeError("Preprocessing returned None")

                with torch.no_grad():
                    logits = model(tensor)
                    probabilities = torch.softmax(logits, dim=1).squeeze().tolist()

                class_idx = probabilities.index(max(probabilities))
                lithology = LITHOLOGY_CLASSES[class_idx]
                confidence = probabilities[class_idx]

                top_predictions = sorted(
                    [
                        {"class": cls, "confidence": round(prob, 4)}
                        for cls, prob in zip(LITHOLOGY_CLASSES, probabilities)
                    ],
                    key=lambda x: x["confidence"],
                    reverse=True,
                )[:5]

                minerals = MINERAL_ASSOCIATIONS.get(lithology, {})

                elapsed = time.perf_counter() - start_time
                return {
                    "rock_type": ROCK_TYPE_MAP.get(lithology, "Unknown"),
                    "lithology_class": lithology,
                    "mineral_predictions": minerals,
                    "confidence_score": round(confidence, 4),
                    "top_predictions": top_predictions,
                    "preprocessing_info": preprocessing_info,
                    "model_used": model_name,
                    "processing_time": round(elapsed, 4),
                    "mock": False,
                }

            except Exception as exc:
                logger.warning(
                    "Real inference failed for '%s' with model '%s': %s — using mock",
                    image_path, model_name, exc,
                )

        # Fallback
        result = self._mock_predict(image_path, model_name)
        elapsed = time.perf_counter() - start_time
        result["preprocessing_info"] = preprocessing_info
        result["processing_time"] = round(elapsed, 4)
        return result


# ── Module-level singleton ────────────────────────────────────────────────────
ml_service = MLService()
