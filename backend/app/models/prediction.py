"""
SQLAlchemy ORM model for ML inference predictions.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)

    # Foreign key
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # File information
    image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)

    # Processing status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending", index=True
    )
    # status values: pending | processing | completed | failed

    # Prediction results
    rock_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lithology_class: Mapped[str | None] = mapped_column(String(100), nullable=True)
    mineral_predictions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    top_predictions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    preprocessing_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Model metadata
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    processing_time: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Error info
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="predictions")  # type: ignore[name-defined]  # noqa: F821
    reports: Mapped[list["Report"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Report", back_populates="prediction", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Prediction id={self.id} status={self.status!r} "
            f"lithology={self.lithology_class!r}>"
        )
