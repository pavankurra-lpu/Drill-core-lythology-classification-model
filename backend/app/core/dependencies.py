"""
FastAPI dependency injection: database sessions, authenticated users, pagination.
"""
from __future__ import annotations

import logging
from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import oauth2_scheme, verify_token
from app.database.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


# ── Database session ──────────────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an async SQLAlchemy session and guarantee cleanup.
    Use as a FastAPI dependency.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Auth dependencies ─────────────────────────────────────────────────────────

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Decode JWT, load the matching User from the DB, and return it.
    Raises HTTP 401 on any auth failure.
    """
    # Import here to avoid circular imports
    from app.models.user import User  # noqa: PLC0415

    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token, token_type="access")
    if payload is None:
        raise credentials_exc

    user_id_str: Optional[str] = payload.get("sub")
    if user_id_str is None:
        raise credentials_exc

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise credentials_exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        logger.warning("Token references non-existent user_id=%s", user_id)
        raise credentials_exc

    return user


async def get_current_active_user(
    current_user=Depends(get_current_user),
):
    """
    Return the current authenticated user only if their account is active.
    Raises HTTP 400 if the account is deactivated.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )
    return current_user


async def get_current_admin_user(
    current_user=Depends(get_current_active_user),
):
    """
    Ensure the current user has the 'admin' role.
    Raises HTTP 403 if not.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required",
        )
    return current_user


# ── Pagination ────────────────────────────────────────────────────────────────

class PaginationParams:
    """Common pagination query parameters injected by dependency."""

    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
        page_size: int = Query(
            default=20, ge=1, le=100, description="Items per page"
        ),
    ) -> None:
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size
