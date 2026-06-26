"""
Pydantic V2 schemas for Analytics endpoints.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PredictionStats(BaseModel):
    total: int
    completed: int
    failed: int
    pending: int
    processing: int
    success_rate: float


class ModelPerformance(BaseModel):
    model_name: str
    accuracy: Optional[float] = None
    total_predictions: int
    avg_confidence: Optional[float] = None
    avg_processing_time_ms: Optional[float] = None


class AnalyticsOverview(BaseModel):
    total_users: int
    active_users: int
    total_predictions: int
    completed_predictions: int
    total_datasets: int
    total_reports: int
    prediction_stats: PredictionStats
    top_lithology_classes: List[Dict[str, Any]]
    recent_activity_count: int


class TimelineDataPoint(BaseModel):
    date: date
    count: int
    completed: int
    failed: int


class PredictionTimelineResponse(BaseModel):
    days: int
    data: List[TimelineDataPoint]


class LithologyDistributionItem(BaseModel):
    lithology_class: str
    count: int
    percentage: float


class LithologyDistributionResponse(BaseModel):
    items: List[LithologyDistributionItem]
    total: int


class ModelComparisonItem(BaseModel):
    model_name: str
    total_predictions: int
    avg_confidence: Optional[float]
    avg_processing_time_ms: Optional[float]
    success_rate: float


class ModelComparisonResponse(BaseModel):
    models: List[ModelComparisonItem]


class UserActivityItem(BaseModel):
    user_id: int
    username: str
    prediction_count: int
    last_active: Optional[str]


class UserActivityResponse(BaseModel):
    items: List[UserActivityItem]
    total_active_users: int
