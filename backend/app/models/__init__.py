"""
Models package — import all models so Alembic autogenerate picks them up.
"""
from app.models.user import User  # noqa: F401
from app.models.prediction import Prediction  # noqa: F401
from app.models.dataset import Dataset  # noqa: F401
from app.models.report import Report  # noqa: F401
from app.models.chat import ChatSession, ChatMessage  # noqa: F401

__all__ = [
    "User",
    "Prediction",
    "Dataset",
    "Report",
    "ChatSession",
    "ChatMessage",
]
