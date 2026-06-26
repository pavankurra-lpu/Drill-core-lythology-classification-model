"""
Analytics router — overview, timeline, lithology distribution, model comparison, user activity.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsOverview,
    LithologyDistributionResponse,
    ModelComparisonResponse,
    PredictionTimelineResponse,
    UserActivityResponse,
)
from app.services.analytics_service import analytics_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/overview",
    response_model=AnalyticsOverview,
    summary="System-wide analytics overview",
)
async def get_overview(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsOverview:
    """Return a high-level analytics summary: totals, stats, top classes."""
    return await analytics_service.get_overview(db)


@router.get(
    "/predictions/timeline",
    response_model=PredictionTimelineResponse,
    summary="Prediction volume over time (daily buckets)",
)
async def get_prediction_timeline(
    days: int = Query(default=30, ge=1, le=365, description="Number of past days"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PredictionTimelineResponse:
    return await analytics_service.get_prediction_timeline(db, days=days)


@router.get(
    "/lithology/distribution",
    response_model=LithologyDistributionResponse,
    summary="Distribution of predicted lithology classes",
)
async def get_lithology_distribution(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> LithologyDistributionResponse:
    return await analytics_service.get_lithology_distribution(db)


@router.get(
    "/models/comparison",
    response_model=ModelComparisonResponse,
    summary="Performance comparison across models",
)
async def get_model_comparison(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ModelComparisonResponse:
    return await analytics_service.get_model_comparison(db)


@router.get(
    "/users/activity",
    response_model=UserActivityResponse,
    summary="User activity statistics (top active users)",
)
async def get_user_activity(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserActivityResponse:
    return await analytics_service.get_user_activity(db)
