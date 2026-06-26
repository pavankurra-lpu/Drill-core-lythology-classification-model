"""
Pydantic V2 schemas for Chatbot endpoints.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Session ───────────────────────────────────────────────────────────────────

class ChatSessionCreate(BaseModel):
    title: str = Field(default="New Chat", max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    prediction_id: Optional[int] = None


class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    description: Optional[str]
    prediction_id: Optional[int]
    created_at: datetime
    updated_at: datetime


class ChatSessionListResponse(BaseModel):
    items: List[ChatSessionResponse]
    total: int


# ── Messages ──────────────────────────────────────────────────────────────────

class ChatMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=10000)
    use_rag: bool = Field(default=True, description="Use RAG context when available")


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    role: str
    content: str
    metadata_: Optional[Dict[str, Any]] = None
    created_at: datetime


class ChatMessagesListResponse(BaseModel):
    session_id: int
    messages: List[ChatMessageResponse]
    total: int


# ── RAG / Search ──────────────────────────────────────────────────────────────

class RAGSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    k: int = Field(default=5, ge=1, le=20)


class RAGSearchResult(BaseModel):
    content: str
    score: float
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class RAGSearchResponse(BaseModel):
    query: str
    results: List[RAGSearchResult]
    total: int
