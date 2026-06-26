"""
Pydantic V2 schemas for Prediction endpoints.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Request schemas ───────────────────────────────────────────────────────────

class PredictionCreate(BaseModel):
    model_used: Optional[str] = Field(default="efficientnet", description="Model to use")


# ── Response schemas ──────────────────────────────────────────────────────────

class MineralPrediction(BaseModel):
    mineral: str
    percentage: float
    confidence: float


class PredictionResult(BaseModel):
    """Embedded prediction output (nested in PredictionResponse)."""
    rock_type: Optional[str] = None
    lithology_class: Optional[str] = None
    mineral_predictions: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    top_predictions: Optional[List[Dict[str, Any]]] = None
    preprocessing_info: Optional[Dict[str, Any]] = None
    model_used: Optional[str] = None
    processing_time: Optional[float] = None


class PredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    image_path: str
    original_filename: str
    status: str
    rock_type: Optional[str]
    lithology_class: Optional[str]
    mineral_predictions: Optional[Dict[str, Any]]
    confidence_score: Optional[float]
    top_predictions: Optional[List[Dict[str, Any]]]
    preprocessing_info: Optional[Dict[str, Any]]
    model_used: Optional[str]
    processing_time: Optional[float]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime


class PredictionListResponse(BaseModel):
    items: List[PredictionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PredictionStatusResponse(BaseModel):
    id: int
    status: str
    message: str
