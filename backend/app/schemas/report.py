"""
Pydantic V2 schemas for Report endpoints.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ReportCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: Optional[str] = None
    report_type: str = Field(default="pdf")


class ReportGenerateRequest(BaseModel):
    prediction_id: int
    title: str = Field(min_length=1, max_length=255)
    include_images: bool = True
    include_analysis: bool = True
    include_mineral_chart: bool = True
    additional_notes: Optional[str] = Field(default=None, max_length=5000)


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    prediction_id: Optional[int]
    title: str
    content: Optional[str]
    report_type: str
    pdf_path: Optional[str]
    created_at: datetime
    updated_at: datetime


class ReportListResponse(BaseModel):
    items: List[ReportResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
