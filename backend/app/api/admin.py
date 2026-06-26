"""
Admin router — user management, system stats, and model retraining.
Admin access required for all endpoints.
"""
from __future__ import annotations

import logging
import math
import platform
import sys
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import PaginationParams, get_current_admin_user, get_db
from app.models.dataset import Dataset
from app.models.prediction import Prediction
from app.models.report import Report
from app.models.user import User
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])


# ── User management ───────────────────────────────────────────────────────────

@router.get(
    "/users",
    summary="List all users (admin only)",
)
async def list_users(
    pagination: PaginationParams = Depends(),
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    count_result = await db.execute(select(func.count(User.id)))
    total = count_result.scalar_one()

    result = await db.execute(
        select(User)
        .order_by(User.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
    )
    users = result.scalars().all()

    return {
        "items": [UserResponse.model_validate(u) for u in users],
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "total_pages": math.ceil(total / pagination.page_size) if total else 1,
    }


@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Update a user account (admin only)",
)
async def admin_update_user(
    user_id: int,
    updates: dict,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    allowed_fields = {"full_name", "role", "is_active", "avatar_url", "username"}
    for field, value in updates.items():
        if field in allowed_fields:
            setattr(user, field, value)

    await db.flush()
    await db.refresh(user)
    logger.info("Admin updated user: user_id=%s by admin_id=%s", user_id, admin.id)
    return UserResponse.model_validate(user)


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user and all their data (admin only)",
)
async def admin_delete_user(
    user_id: int,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await db.delete(user)
    logger.warning("Admin deleted user: user_id=%s by admin_id=%s", user_id, admin.id)


# ── Predictions (all users) ───────────────────────────────────────────────────

@router.get(
    "/predictions",
    summary="List all predictions across all users (admin only)",
)
async def admin_list_predictions(
    pagination: PaginationParams = Depends(),
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.schemas.prediction import PredictionResponse  # noqa: PLC0415

    count_result = await db.execute(select(func.count(Prediction.id)))
    total = count_result.scalar_one()

    result = await db.execute(
        select(Prediction)
        .order_by(Prediction.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
    )
    predictions = result.scalars().all()

    return {
        "items": [PredictionResponse.model_validate(p) for p in predictions],
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "total_pages": math.ceil(total / pagination.page_size) if total else 1,
    }


# ── System stats ──────────────────────────────────────────────────────────────

@router.get(
    "/system/stats",
    summary="System-wide statistics and health metrics (admin only)",
)
async def get_system_stats(
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return aggregate system stats: user counts, prediction totals, disk info, etc."""
    total_users = (await db.execute(select(func.count(User.id)))).scalar_one()
    active_users = (await db.execute(
        select(func.count(User.id)).where(User.is_active == True)  # noqa: E712
    )).scalar_one()

    total_predictions = (await db.execute(select(func.count(Prediction.id)))).scalar_one()
    completed_predictions = (await db.execute(
        select(func.count(Prediction.id)).where(Prediction.status == "completed")
    )).scalar_one()
    failed_predictions = (await db.execute(
        select(func.count(Prediction.id)).where(Prediction.status == "failed")
    )).scalar_one()

    total_datasets = (await db.execute(select(func.count(Dataset.id)))).scalar_one()
    total_reports = (await db.execute(select(func.count(Report.id)))).scalar_one()

    # New users last 7 days
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    new_users_week = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= cutoff)
    )).scalar_one()

    import shutil  # noqa: PLC0415
    disk = shutil.disk_usage(".")
    disk_info = {
        "total_gb": round(disk.total / (1024 ** 3), 2),
        "used_gb": round(disk.used / (1024 ** 3), 2),
        "free_gb": round(disk.free / (1024 ** 3), 2),
        "usage_percent": round(disk.used / disk.total * 100, 1),
    }

    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "new_this_week": new_users_week,
        },
        "predictions": {
            "total": total_predictions,
            "completed": completed_predictions,
            "failed": failed_predictions,
            "success_rate": round(
                (completed_predictions / total_predictions * 100) if total_predictions else 0, 2
            ),
        },
        "datasets": total_datasets,
        "reports": total_reports,
        "system": {
            "python_version": sys.version,
            "platform": platform.platform(),
            "disk": disk_info,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Model retraining ──────────────────────────────────────────────────────────

@router.post(
    "/models/retrain",
    summary="Trigger model retraining on a dataset (admin only)",
)
async def retrain_model(
    dataset_id: int,
    background_tasks: BackgroundTasks,
    model_name: str = "efficientnet",
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Run model retraining as a background task for the given dataset."""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    if dataset.status != "ready" and dataset.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dataset status is '{dataset.status}', must be 'ready' or 'completed'",
        )

    try:
        from app.tasks.training_tasks import async_retrain_model  # noqa: PLC0415

        background_tasks.add_task(async_retrain_model, dataset_id=dataset_id, model_name=model_name)
        logger.info(
            "Retraining background task triggered: dataset_id=%s model=%s",
            dataset_id, model_name,
        )
        return {
            "message": "Retraining task triggered successfully",
            "dataset_id": dataset_id,
            "model_name": model_name,
        }
    except Exception as exc:
        logger.error("Failed to run retraining background task: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not run retraining task: {exc}",
        )
