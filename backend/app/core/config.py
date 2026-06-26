"""
Application configuration using Pydantic BaseSettings.
All settings are read from environment variables with fallbacks.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "Lithology Classification System"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    VERSION: str = "1.0.0"
    DESCRIPTION: str = (
        "Automated Lithology Classification System for Drill Core Samples "
        "using Machine Learning — REST API Backend"
    )

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = (
        "sqlite+aiosqlite:///./lithology.db"
    )
    SYNC_DATABASE_URL: str = (
        "sqlite:///./lithology.db"
    )

    # ── Redis / Celery ────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = "super-secret-key-change-in-production-please-use-32-chars-min"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── File Upload ───────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "uploads"
    REPORTS_DIR: str = "reports"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "tiff", "bmp", "webp"]

    # ── ML Models ─────────────────────────────────────────────────────────────
    MODEL_DIR: str = "models"
    EFFICIENTNET_WEIGHTS: str = "models/efficientnet_lithology.pth"
    RESNET_WEIGHTS: str = "models/resnet50_lithology.pth"
    MOBILENET_WEIGHTS: str = "models/mobilenet_lithology.pth"
    IMAGE_SIZE: int = 224
    NUM_CLASSES: int = 10

    # ── LLM / RAG ─────────────────────────────────────────────────────────────
    LLM_MODEL_NAME: str = "google/flan-t5-base"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    FAISS_INDEX_PATH: str = "faiss_index"
    RAG_TOP_K: int = 5
    MAX_CONTEXT_LENGTH: int = 2048

    # ── AWS (optional) ────────────────────────────────────────────────────────
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET: str = ""

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
    ]

    @field_validator("UPLOAD_DIR", "REPORTS_DIR", "MODEL_DIR", "FAISS_INDEX_PATH", mode="before")
    @classmethod
    def create_dirs(cls, v: str) -> str:
        os.makedirs(v, exist_ok=True)
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()


settings = get_settings()
