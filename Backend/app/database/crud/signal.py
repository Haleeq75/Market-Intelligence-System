"""
app/database/crud/signal.py — TradingSignal CRUD
app/database/crud/user.py   — User CRUD
"""
from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.signal import TradingSignal
from app.database.models.user import User
from app.core.security import hash_password


# ═══════════════════════════════════════════════════════════════════════════════
# TradingSignal CRUD
# ═══════════════════════════════════════════════════════════════════════════════

async def create_signal(
    db: AsyncSession,
    *,
    asset_id: uuid.UUID,
    decision_id: uuid.UUID,
    signal: str,
    bull_confidence: float,
    bear_confidence: float,
    net_confidence: float,
    price_at_signal: float | None = None,
    currency: str = "USD",
) -> TradingSignal:
    s = TradingSignal(
        asset_id=asset_id,
        decision_id=decision_id,
        signal=signal.upper(),
        bull_confidence=Decimal(str(bull_confidence)),
        bear_confidence=Decimal(str(bear_confidence)),
        net_confidence=Decimal(str(net_confidence)),
        price_at_signal=Decimal(str(price_at_signal)) if price_at_signal else None,
        currency=currency,
    )
    db.add(s)
    await db.flush()
    await db.refresh(s)
    return s


async def get_latest_signals(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    ticker: str | None = None,
    limit: int = 50,
) -> list[TradingSignal]:
    q = (
        select(TradingSignal)
        .join(TradingSignal.asset)
        .where(TradingSignal.asset.has(user_id=user_id))
        .options(selectinload(TradingSignal.asset))
        .order_by(desc(TradingSignal.created_at))
        .limit(limit)
    )
    if ticker:
        q = q.where(TradingSignal.asset.has(ticker=ticker.upper()))
    return list((await db.execute(q)).scalars().all())


# ═══════════════════════════════════════════════════════════════════════════════
# User CRUD
# ═══════════════════════════════════════════════════════════════════════════════

async def create_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    full_name: str | None = None,
) -> User:
    user = User(
        email=email.lower().strip(),
        hashed_password=hash_password(password),
        full_name=full_name,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(
        select(User).where(User.email == email.lower().strip())
    )
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
