"""
app/database/crud/asset.py — Asset watchlist CRUD
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.asset import Asset


async def get_assets_for_user(db: AsyncSession, user_id: uuid.UUID) -> list[Asset]:
    result = await db.execute(select(Asset).where(Asset.user_id == user_id).order_by(Asset.ticker))
    return list(result.scalars().all())


async def get_asset_by_ticker(
    db: AsyncSession, user_id: uuid.UUID, ticker: str
) -> Asset | None:
    result = await db.execute(
        select(Asset).where(Asset.user_id == user_id, Asset.ticker == ticker.upper())
    )
    return result.scalar_one_or_none()


async def get_or_create_asset(
    db: AsyncSession, *, user_id: uuid.UUID, ticker: str
) -> Asset:
    existing = await get_asset_by_ticker(db, user_id, ticker)
    if existing:
        return existing
    return await create_asset(db, user_id=user_id, ticker=ticker)


async def create_asset(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    ticker: str,
    name: str | None = None,
    asset_class: str = "equity",
) -> Asset:
    asset = Asset(
        user_id=user_id,
        ticker=ticker.upper(),
        name=name,
        asset_class=asset_class,
    )
    db.add(asset)
    await db.flush()
    await db.refresh(asset)
    return asset


async def delete_asset(
    db: AsyncSession, *, asset_id: uuid.UUID, user_id: uuid.UUID
) -> bool:
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id, Asset.user_id == user_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        return False
    await db.delete(asset)
    return True
