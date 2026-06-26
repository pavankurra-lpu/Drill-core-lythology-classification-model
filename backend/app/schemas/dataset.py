"""
Pydantic V2 schemas for Dataset endpoints.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DatasetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)


class DatasetUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    description: Optional[str]
    file_path: str
    file_size: Optional[int]
    num_samples: Optional[int]
    num_classes: Optional[int]
    classes: Optional[List[str]]
    status: str
    created_at: datetime
    updated_at: datetime


class DatasetListResponse(BaseModel):
    items: List[DatasetResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DatasetSampleResponse(BaseModel):
    """A single sample from a dataset directory listing."""
    filename: str
    class_label: Optional[str]
    file_path: str
    file_size: int
