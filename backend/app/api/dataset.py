"""
Dataset router — upload, list, detail, delete, and sample listing.
"""
from __future__ import annotations

import logging
import math
import os
import uuid
import zipfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import PaginationParams, get_current_active_user, get_db
from app.models.dataset import Dataset
from app.models.user import User
from app.schemas.dataset import (
    DatasetListResponse,
    DatasetResponse,
    DatasetSampleResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/datasets", tags=["Datasets"])

DATASETS_DIR = Path(settings.UPLOAD_DIR) / "datasets"
DATASETS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_ARCHIVE_EXTS = {".zip"}


@router.post(
    "/upload",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a dataset archive (ZIP) for model training/evaluation",
)
async def upload_dataset(
    file: UploadFile = File(..., description="ZIP archive containing images organised by class"),
    name: str = Form(..., min_length=1, max_length=255),
    description: str = Form(default=""),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DatasetResponse:
    """Upload a zipped dataset. Extracts and analyses class structure."""
    filename = file.filename or "dataset.zip"
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_ARCHIVE_EXTS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only ZIP archives are supported",
        )

    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE * 20:  # 1 GB
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Dataset archive is too large",
        )

    # Save archive
    unique_id = uuid.uuid4().hex
    user_ds_dir = DATASETS_DIR / str(current_user.id) / unique_id
    user_ds_dir.mkdir(parents=True, exist_ok=True)
    archive_path = user_ds_dir / filename

    with open(archive_path, "wb") as f:
        f.write(content)

    # Extract and analyse
    extract_dir = user_ds_dir / "extracted"
    extract_dir.mkdir(exist_ok=True)
    classes: List[str] = []
    num_samples = 0

    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(extract_dir)

        # Detect classes from top-level directories
        for entry in sorted(extract_dir.iterdir()):
            if entry.is_dir():
                classes.append(entry.name)
                images = [
                    f for f in entry.iterdir()
                    if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".tiff", ".bmp"}
                ]
                num_samples += len(images)

        if not classes:
            # Try one level deeper
            for sub in sorted(extract_dir.iterdir()):
                if sub.is_dir():
                    for entry in sorted(sub.iterdir()):
                        if entry.is_dir():
                            classes.append(entry.name)
                            images = [
                                f for f in entry.iterdir()
                                if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".tiff", ".bmp"}
                            ]
                            num_samples += len(images)
                    break

    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is not a valid ZIP archive",
        )

    dataset = Dataset(
        user_id=current_user.id,
        name=name,
        description=description or None,
        file_path=str(user_ds_dir),
        file_size=len(content),
        num_samples=num_samples or None,
        num_classes=len(classes) or None,
        classes=classes or None,
        status="ready" if classes else "uploaded",
    )
    db.add(dataset)
    await db.flush()
    await db.refresh(dataset)

    logger.info(
        "Dataset uploaded: id=%s user=%s classes=%d samples=%d",
        dataset.id, current_user.id, len(classes), num_samples,
    )
    return DatasetResponse.model_validate(dataset)


@router.get(
    "/",
    response_model=DatasetListResponse,
    summary="List all datasets for the current user",
)
async def list_datasets(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DatasetListResponse:
    count_result = await db.execute(
        select(func.count(Dataset.id)).where(Dataset.user_id == current_user.id)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Dataset)
        .where(Dataset.user_id == current_user.id)
        .order_by(Dataset.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
    )
    datasets = result.scalars().all()

    return DatasetListResponse(
        items=[DatasetResponse.model_validate(d) for d in datasets],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=math.ceil(total / pagination.page_size) if total else 1,
    )


@router.get(
    "/{dataset_id}",
    response_model=DatasetResponse,
    summary="Get dataset details",
)
async def get_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DatasetResponse:
    result = await db.execute(
        select(Dataset).where(
            Dataset.id == dataset_id, Dataset.user_id == current_user.id
        )
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return DatasetResponse.model_validate(dataset)


@router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a dataset and its files",
)
async def delete_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(Dataset).where(
            Dataset.id == dataset_id, Dataset.user_id == current_user.id
        )
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    # Delete files from disk
    if dataset.file_path and os.path.exists(dataset.file_path):
        import shutil  # noqa: PLC0415

        try:
            shutil.rmtree(dataset.file_path)
        except OSError as exc:
            logger.warning("Could not remove dataset files: %s", exc)

    await db.delete(dataset)
    logger.info("Dataset deleted: id=%s user_id=%s", dataset_id, current_user.id)


@router.get(
    "/{dataset_id}/samples",
    response_model=List[DatasetSampleResponse],
    summary="List sample files inside a dataset",
)
async def list_dataset_samples(
    dataset_id: int,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[DatasetSampleResponse]:
    result = await db.execute(
        select(Dataset).where(
            Dataset.id == dataset_id, Dataset.user_id == current_user.id
        )
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    extract_dir = Path(dataset.file_path) / "extracted"
    if not extract_dir.exists():
        return []

    samples: List[DatasetSampleResponse] = []
    image_extensions = {".jpg", ".jpeg", ".png", ".tiff", ".bmp"}

    for class_dir in sorted(extract_dir.iterdir()):
        if not class_dir.is_dir():
            continue
        for img_file in sorted(class_dir.iterdir()):
            if img_file.suffix.lower() not in image_extensions:
                continue
            samples.append(
                DatasetSampleResponse(
                    filename=img_file.name,
                    class_label=class_dir.name,
                    file_path=str(img_file),
                    file_size=img_file.stat().st_size,
                )
            )
            if len(samples) >= limit:
                return samples

    return samples
