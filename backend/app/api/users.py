"""
Users router — current user profile management, password change, avatar upload.
"""
from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_active_user, get_db
from app.core.security import get_password_hash, verify_password
from app.models.prediction import Prediction
from app.models.report import Report
from app.models.dataset import Dataset
from app.models.user import User
from app.schemas.user import UserPasswordUpdate, UserResponse, UserStatsResponse, UserUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["Users"])

AVATARS_DIR = Path(settings.UPLOAD_DIR) / "avatars"
AVATARS_DIR.mkdir(parents=True, exist_ok=True)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
)
async def update_me(
    updates: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    update_data = updates.model_dump(exclude_none=True)

    # Check username uniqueness if changed
    if "username" in update_data and update_data["username"] != current_user.username:
        existing = await db.execute(
            select(User).where(User.username == update_data["username"])
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )

    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.flush()
    await db.refresh(current_user)
    logger.info("User profile updated: user_id=%s", current_user.id)
    return UserResponse.model_validate(current_user)


@router.put(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change current user's password",
)
async def change_password(
    body: UserPasswordUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    current_user.hashed_password = get_password_hash(body.new_password)
    await db.flush()
    logger.info("Password changed for user_id=%s", current_user.id)


@router.post(
    "/me/avatar",
    response_model=UserResponse,
    summary="Upload a user profile avatar",
)
async def upload_avatar(
    file: UploadFile = File(..., description="Image file for the avatar"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    allowed_exts = {"jpg", "jpeg", "png", "webp", "gif"}
    fname = file.filename or "avatar.png"
    ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else "png"
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '.{ext}' not allowed for avatars",
        )

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:  # 5 MB limit for avatars
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Avatar image must be less than 5 MB",
        )

    unique_name = f"{current_user.id}_{uuid.uuid4().hex}.{ext}"
    avatar_path = AVATARS_DIR / unique_name

    with open(avatar_path, "wb") as f:
        f.write(content)

    current_user.avatar_url = f"/static/avatars/{unique_name}"
    await db.flush()
    await db.refresh(current_user)

    logger.info("Avatar updated for user_id=%s", current_user.id)
    return UserResponse.model_validate(current_user)


@router.get(
    "/me/stats",
    response_model=UserStatsResponse,
    summary="Get statistics for the current user",
)
async def get_user_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserStatsResponse:
    total_preds = (await db.execute(
        select(func.count(Prediction.id)).where(Prediction.user_id == current_user.id)
    )).scalar_one()

    completed_preds = (await db.execute(
        select(func.count(Prediction.id)).where(
            Prediction.user_id == current_user.id, Prediction.status == "completed"
        )
    )).scalar_one()

    failed_preds = (await db.execute(
        select(func.count(Prediction.id)).where(
            Prediction.user_id == current_user.id, Prediction.status == "failed"
        )
    )).scalar_one()

    total_reports = (await db.execute(
        select(func.count(Report.id)).where(Report.user_id == current_user.id)
    )).scalar_one()

    total_datasets = (await db.execute(
        select(func.count(Dataset.id)).where(Dataset.user_id == current_user.id)
    )).scalar_one()

    return UserStatsResponse(
        total_predictions=total_preds,
        completed_predictions=completed_preds,
        failed_predictions=failed_preds,
        total_reports=total_reports,
        total_datasets=total_datasets,
        member_since=current_user.created_at,
    )
