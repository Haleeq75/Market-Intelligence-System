"""
app/core/dependencies.py
────────────────────────
FastAPI Depends() providers for DB session, current user, and pagination.
"""
from __future__ import annotations

from typing import Annotated, AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import validate_access_token
from app.database.session import async_session_factory
from app.database.crud.user import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


# ── Database session ───────────────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async DB session, auto-commit on success, rollback on error."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


DbSession = Annotated[AsyncSession, Depends(get_db)]


# ── Auth ───────────────────────────────────────────────────────────────────────

async def get_current_user_id(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> UUID:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id_str = validate_access_token(token)
        return UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exc


async def get_current_user(
    db: DbSession,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
):
    from app.database.models.user import User
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user


CurrentUser = Annotated[any, Depends(get_current_user)]


# ── Pagination ─────────────────────────────────────────────────────────────────

class PaginationParams:
    def __init__(
        self,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100),
    ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size


Pagination = Annotated[PaginationParams, Depends(PaginationParams)]
