"""
History router — paginated prediction history, stats, clear, and CSV export.
"""
from __future__ import annotations

import csv
import io
import logging
import math
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import PaginationParams, get_current_active_user, get_db
from app.models.prediction import Prediction
from app.models.user import User
from app.schemas.prediction import PredictionListResponse, PredictionResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/history", tags=["History"])


@router.get(
    "/",
    response_model=PredictionListResponse,
    summary="Paginated prediction history for the current user",
)
async def get_history(
    pagination: PaginationParams = Depends(),
    status_filter: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PredictionListResponse:
    """Return paginated prediction history, optionally filtered by status."""
    query = select(Prediction).where(Prediction.user_id == current_user.id)
    count_query = select(func.count(Prediction.id)).where(
        Prediction.user_id == current_user.id
    )

    if status_filter:
        query = query.where(Prediction.status == status_filter)
        count_query = count_query.where(Prediction.status == status_filter)

    total = (await db.execute(count_query)).scalar_one()

    result = await db.execute(
        query.order_by(Prediction.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
    )
    predictions = result.scalars().all()

    return PredictionListResponse(
        items=[PredictionResponse.model_validate(p) for p in predictions],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=math.ceil(total / pagination.page_size) if total else 1,
    )


@router.get(
    "/stats",
    summary="Prediction statistics for the current user",
)
async def get_history_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return aggregate statistics about the user's prediction history."""
    base_where = Prediction.user_id == current_user.id

    total = (await db.execute(
        select(func.count(Prediction.id)).where(base_where)
    )).scalar_one()

    completed = (await db.execute(
        select(func.count(Prediction.id)).where(base_where, Prediction.status == "completed")
    )).scalar_one()

    failed = (await db.execute(
        select(func.count(Prediction.id)).where(base_where, Prediction.status == "failed")
    )).scalar_one()

    pending = (await db.execute(
        select(func.count(Prediction.id)).where(base_where, Prediction.status == "pending")
    )).scalar_one()

    avg_conf_result = await db.execute(
        select(func.avg(Prediction.confidence_score)).where(
            base_where, Prediction.status == "completed"
        )
    )
    avg_confidence = avg_conf_result.scalar_one()

    # Last 30 days
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    recent = (await db.execute(
        select(func.count(Prediction.id)).where(
            base_where, Prediction.created_at >= cutoff
        )
    )).scalar_one()

    return {
        "total_predictions": total,
        "completed": completed,
        "failed": failed,
        "pending": pending,
        "processing": total - completed - failed - pending,
        "success_rate": round((completed / total * 100) if total else 0, 2),
        "avg_confidence": round(float(avg_confidence), 4) if avg_confidence else None,
        "last_30_days": recent,
    }


@router.delete(
    "/clear",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete all prediction history for the current user",
)
async def clear_history(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete ALL predictions (and their image files) belonging to the current user."""
    import os  # noqa: PLC0415

    result = await db.execute(
        select(Prediction).where(Prediction.user_id == current_user.id)
    )
    predictions = result.scalars().all()

    for p in predictions:
        if p.image_path and os.path.exists(p.image_path):
            try:
                os.remove(p.image_path)
            except OSError:
                pass
        await db.delete(p)

    logger.info("History cleared for user_id=%s (%d records)", current_user.id, len(predictions))


@router.get(
    "/export",
    summary="Export prediction history as CSV",
)
async def export_history(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Download the full prediction history as a CSV file."""
    result = await db.execute(
        select(Prediction)
        .where(Prediction.user_id == current_user.id)
        .order_by(Prediction.created_at.desc())
    )
    predictions = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "original_filename", "status", "rock_type", "lithology_class",
        "confidence_score", "model_used", "processing_time_s",
        "created_at", "updated_at",
    ])

    for p in predictions:
        writer.writerow([
            p.id,
            p.original_filename,
            p.status,
            p.rock_type or "",
            p.lithology_class or "",
            p.confidence_score if p.confidence_score is not None else "",
            p.model_used or "",
            p.processing_time if p.processing_time is not None else "",
            p.created_at.isoformat() if p.created_at else "",
            p.updated_at.isoformat() if p.updated_at else "",
        ])

    output.seek(0)
    filename = f"predictions_user_{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
