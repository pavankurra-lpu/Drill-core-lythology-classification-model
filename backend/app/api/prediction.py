"""
Prediction router — image upload, status polling, list, delete, rerun.
"""
from __future__ import annotations

import logging
import math
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status, BackgroundTasks
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import PaginationParams, get_current_active_user, get_db
from app.models.prediction import Prediction
from app.models.user import User
from app.schemas.prediction import (
    PredictionListResponse,
    PredictionResponse,
    PredictionStatusResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/predictions", tags=["Predictions"])

ALLOWED_MIMES = {
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/bmp",
    "image/webp",
}


def _validate_extension(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File extension '.{ext}' not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}",
        )
    return ext


@router.post(
    "/upload",
    response_model=PredictionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload an image for lithology classification",
)
async def upload_prediction(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Rock core image (jpg/png/tiff/bmp/webp)"),
    model_used: str = Form(default="efficientnet"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PredictionResponse:
    """
    Upload an image file, save it to disk, and run background inference.
    Returns the pending prediction record immediately.
    """
    if file.size and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum allowed size: {settings.MAX_FILE_SIZE // (1024*1024)} MB",
        )

    ext = _validate_extension(file.filename or "image.jpg")

    # Build unique storage path
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    user_dir = Path(settings.UPLOAD_DIR) / str(current_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    file_path = user_dir / unique_name

    # Stream file to disk
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large after reading",
        )

    with open(file_path, "wb") as f:
        f.write(content)

    logger.info(
        "File saved: user_id=%s path=%s size=%d bytes",
        current_user.id,
        file_path,
        len(content),
    )

    # Persist prediction record
    prediction = Prediction(
        user_id=current_user.id,
        image_path=str(file_path),
        original_filename=file.filename or unique_name,
        status="pending",
        model_used=model_used,
    )
    db.add(prediction)
    await db.flush()
    await db.refresh(prediction)

    # Run BackgroundTask
    try:
        from app.tasks.prediction_tasks import async_process_prediction  # noqa: PLC0415
        background_tasks.add_task(async_process_prediction, prediction.id)
        logger.info("Enqueued background prediction task for prediction_id=%s", prediction.id)
    except Exception as exc:
        logger.error("Could not trigger background task: %s", exc)

    return PredictionResponse.model_validate(prediction)


@router.get(
    "/",
    response_model=PredictionListResponse,
    summary="List all predictions for the current user",
)
async def list_predictions(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PredictionListResponse:
    """Return a paginated list of the current user's predictions."""
    count_result = await db.execute(
        select(func.count(Prediction.id)).where(Prediction.user_id == current_user.id)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Prediction)
        .where(Prediction.user_id == current_user.id)
        .order_by(Prediction.created_at.desc())
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
    "/{prediction_id}",
    response_model=PredictionResponse,
    summary="Get a single prediction by ID",
)
async def get_prediction(
    prediction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PredictionResponse:
    """Retrieve full prediction details, including ML results once completed."""
    result = await db.execute(
        select(Prediction).where(
            Prediction.id == prediction_id,
            Prediction.user_id == current_user.id,
        )
    )
    prediction = result.scalar_one_or_none()
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found",
        )
    return PredictionResponse.model_validate(prediction)


@router.delete(
    "/{prediction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a prediction and its image",
)
async def delete_prediction(
    prediction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a prediction record and remove the associated image file."""
    result = await db.execute(
        select(Prediction).where(
            Prediction.id == prediction_id,
            Prediction.user_id == current_user.id,
        )
    )
    prediction = result.scalar_one_or_none()
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found",
        )

    # Remove file from disk
    if prediction.image_path and os.path.exists(prediction.image_path):
        try:
            os.remove(prediction.image_path)
        except OSError as exc:
            logger.warning("Could not delete image file: %s", exc)

    await db.delete(prediction)
    logger.info("Prediction deleted: id=%s user_id=%s", prediction_id, current_user.id)


@router.post(
    "/{prediction_id}/rerun",
    response_model=PredictionStatusResponse,
    summary="Re-run inference on an existing prediction",
)
async def rerun_prediction(
    prediction_id: int,
    model_used: str = Form(default="efficientnet"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PredictionStatusResponse:
    """Reset a prediction to pending status and enqueue it for re-processing."""
    result = await db.execute(
        select(Prediction).where(
            Prediction.id == prediction_id,
            Prediction.user_id == current_user.id,
        )
    )
    prediction = result.scalar_one_or_none()
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found",
        )

    if prediction.status == "processing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Prediction is currently being processed",
        )

    prediction.status = "pending"
    prediction.model_used = model_used
    prediction.error_message = None
    await db.flush()

    try:
        from app.tasks.prediction_tasks import process_prediction  # noqa: PLC0415

        process_prediction.delay(prediction.id)
    except Exception as exc:
        logger.warning("Could not enqueue rerun task: %s", exc)

    return PredictionStatusResponse(
        id=prediction.id,
        status="pending",
        message="Prediction re-queued for processing",
    )
