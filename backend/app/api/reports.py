"""
Reports router — generate, list, view, download PDF, and delete reports.
"""
from __future__ import annotations

import logging
import math
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import PaginationParams, get_current_active_user, get_db
from app.models.prediction import Prediction
from app.models.report import Report
from app.models.user import User
from app.schemas.report import (
    ReportGenerateRequest,
    ReportListResponse,
    ReportResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post(
    "/generate",
    response_model=ReportResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate a PDF report for a prediction",
)
async def generate_report(
    request: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    """
    Generate a professional PDF report for a completed prediction.
    Runs a background task; returns the pending report record immediately.
    """
    # Verify the prediction exists and belongs to the user
    pred_result = await db.execute(
        select(Prediction).where(
            Prediction.id == request.prediction_id,
            Prediction.user_id == current_user.id,
        )
    )
    prediction = pred_result.scalar_one_or_none()
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found",
        )

    if prediction.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot generate report: prediction status is '{prediction.status}'",
        )

    report = Report(
        user_id=current_user.id,
        prediction_id=prediction.id,
        title=request.title,
        content=request.additional_notes,
        report_type="pdf",
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)

    # Run BackgroundTask
    try:
        from app.tasks.report_tasks import async_generate_report_task  # noqa: PLC0415
        background_tasks.add_task(async_generate_report_task, report.id)
        logger.info("Report generation background task enqueued: report_id=%s", report.id)
    except Exception as exc:
        logger.warning("Could not run background report task: %s", exc)

    return ReportResponse.model_validate(report)


@router.get(
    "/",
    response_model=ReportListResponse,
    summary="List all reports for the current user",
)
async def list_reports(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ReportListResponse:
    count_result = await db.execute(
        select(func.count(Report.id)).where(Report.user_id == current_user.id)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Report)
        .where(Report.user_id == current_user.id)
        .order_by(Report.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
    )
    reports = result.scalars().all()

    return ReportListResponse(
        items=[ReportResponse.model_validate(r) for r in reports],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=math.ceil(total / pagination.page_size) if total else 1,
    )


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Get report details",
)
async def get_report(
    report_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    result = await db.execute(
        select(Report).where(
            Report.id == report_id, Report.user_id == current_user.id
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return ReportResponse.model_validate(report)


@router.get(
    "/{report_id}/download",
    summary="Download the PDF report",
)
async def download_report(
    report_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Stream the PDF file as a download response."""
    result = await db.execute(
        select(Report).where(
            Report.id == report_id, Report.user_id == current_user.id
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    if not report.pdf_path or not os.path.exists(report.pdf_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file not available yet. Please try again shortly.",
        )

    return FileResponse(
        path=report.pdf_path,
        media_type="application/pdf",
        filename=f"report_{report.id}_{report.title.replace(' ', '_')}.pdf",
    )


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a report",
)
async def delete_report(
    report_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(Report).where(
            Report.id == report_id, Report.user_id == current_user.id
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    if report.pdf_path and os.path.exists(report.pdf_path):
        try:
            os.remove(report.pdf_path)
        except OSError as exc:
            logger.warning("Could not remove PDF file: %s", exc)

    await db.delete(report)
    logger.info("Report deleted: id=%s user_id=%s", report_id, current_user.id)
