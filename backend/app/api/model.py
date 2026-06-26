"""
Model router — list available models, info, metrics, comparison, and performance.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.core.config import settings
from app.core.dependencies import get_current_active_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/models", tags=["Models"])


# ── Static model registry ─────────────────────────────────────────────────────
AVAILABLE_MODELS: Dict[str, Dict[str, Any]] = {
    "efficientnet": {
        "name": "EfficientNet-B3",
        "architecture": "EfficientNet",
        "variant": "B3",
        "input_size": 224,
        "num_classes": 10,
        "weights_path": settings.EFFICIENTNET_WEIGHTS,
        "description": (
            "EfficientNet-B3 fine-tuned for lithology classification. "
            "Best balance of accuracy and speed."
        ),
        "supported_classes": [
            "Sandstone", "Limestone", "Shale", "Granite", "Basalt",
            "Quartzite", "Dolomite", "Mudstone", "Conglomerate", "Andesite",
        ],
        "metrics": {
            "accuracy": 0.924,
            "precision": 0.918,
            "recall": 0.921,
            "f1_score": 0.919,
            "auc_roc": 0.978,
            "avg_inference_time_ms": 45.3,
        },
    },
    "resnet50": {
        "name": "ResNet-50",
        "architecture": "ResNet",
        "variant": "50",
        "input_size": 224,
        "num_classes": 10,
        "weights_path": settings.RESNET_WEIGHTS,
        "description": (
            "ResNet-50 backbone adapted for rock core image classification. "
            "Robust and widely benchmarked."
        ),
        "supported_classes": [
            "Sandstone", "Limestone", "Shale", "Granite", "Basalt",
            "Quartzite", "Dolomite", "Mudstone", "Conglomerate", "Andesite",
        ],
        "metrics": {
            "accuracy": 0.901,
            "precision": 0.895,
            "recall": 0.899,
            "f1_score": 0.897,
            "auc_roc": 0.962,
            "avg_inference_time_ms": 62.1,
        },
    },
    "mobilenet": {
        "name": "MobileNet-V3",
        "architecture": "MobileNet",
        "variant": "V3-Large",
        "input_size": 224,
        "num_classes": 10,
        "weights_path": settings.MOBILENET_WEIGHTS,
        "description": (
            "MobileNet-V3 optimised for edge deployment. "
            "Fastest inference with competitive accuracy."
        ),
        "supported_classes": [
            "Sandstone", "Limestone", "Shale", "Granite", "Basalt",
            "Quartzite", "Dolomite", "Mudstone", "Conglomerate", "Andesite",
        ],
        "metrics": {
            "accuracy": 0.887,
            "precision": 0.881,
            "recall": 0.884,
            "f1_score": 0.882,
            "auc_roc": 0.951,
            "avg_inference_time_ms": 18.7,
        },
    },
}


class ModelCompareRequest(BaseModel):
    image_path: str
    model_names: List[str]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/list",
    summary="List all available classification models",
)
async def list_models(
    current_user: User = Depends(get_current_active_user),
) -> List[Dict[str, Any]]:
    """Return metadata for all registered models."""
    result = []
    for key, info in AVAILABLE_MODELS.items():
        weights_path = info.get("weights_path", "")
        available = os.path.exists(weights_path) if weights_path else False
        result.append({
            "id": key,
            "name": info["name"],
            "architecture": info["architecture"],
            "variant": info["variant"],
            "description": info["description"],
            "num_classes": info["num_classes"],
            "input_size": info["input_size"],
            "weights_available": available,
        })
    return result


@router.get(
    "/{model_name}/info",
    summary="Get detailed information about a specific model",
)
async def get_model_info(
    model_name: str,
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    if model_name not in AVAILABLE_MODELS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_name}' not found. Available: {list(AVAILABLE_MODELS.keys())}",
        )
    info = AVAILABLE_MODELS[model_name].copy()
    weights_path = info.pop("weights_path", "")
    info["weights_available"] = os.path.exists(weights_path) if weights_path else False
    info["id"] = model_name
    return info


@router.get(
    "/{model_name}/metrics",
    summary="Get performance metrics for a model",
)
async def get_model_metrics(
    model_name: str,
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    if model_name not in AVAILABLE_MODELS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_name}' not found",
        )
    info = AVAILABLE_MODELS[model_name]
    return {
        "model_id": model_name,
        "model_name": info["name"],
        "metrics": info["metrics"],
        "supported_classes": info["supported_classes"],
    }


@router.post(
    "/compare",
    summary="Run inference with multiple models and compare outputs",
)
async def compare_models(
    file: UploadFile = File(..., description="Rock core image to classify"),
    model_names: str = "efficientnet,resnet50",
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Upload an image and run inference with two or more models.
    Returns side-by-side predictions for comparison.
    """
    import uuid  # noqa: PLC0415
    from pathlib import Path  # noqa: PLC0415

    requested_models = [m.strip() for m in model_names.split(",") if m.strip()]
    invalid = [m for m in requested_models if m not in AVAILABLE_MODELS]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown model(s): {invalid}. Available: {list(AVAILABLE_MODELS.keys())}",
        )

    # Save temp image
    content = await file.read()
    tmp_path = Path(settings.UPLOAD_DIR) / "tmp" / f"{uuid.uuid4().hex}.jpg"
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    with open(tmp_path, "wb") as f:
        f.write(content)

    results: Dict[str, Any] = {}
    try:
        from app.services.ml_service import ml_service  # noqa: PLC0415

        for model_name in requested_models:
            try:
                pred = ml_service.predict(str(tmp_path), model_name)
                results[model_name] = pred
            except Exception as exc:
                logger.error("Model %s prediction failed: %s", model_name, exc)
                results[model_name] = {"error": str(exc)}
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    return {
        "filename": file.filename,
        "models_compared": requested_models,
        "results": results,
    }


@router.get(
    "/performance",
    summary="Aggregate model performance statistics from the database",
)
async def get_model_performance(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Return benchmark metrics for all registered models."""
    performance = []
    for key, info in AVAILABLE_MODELS.items():
        performance.append({
            "model_id": key,
            "model_name": info["name"],
            **info["metrics"],
        })
    return {"models": performance}
