"""
app/database/crud/decision.py
──────────────────────────────
CRUD operations for Decision Journal entries.
Includes pgvector cosine-similarity search for surfacing
relevant past decisions during agent analysis.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.decision import Decision


# ── Create ─────────────────────────────────────────────────────────────────────

async def create_decision(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    ticker: str,
) -> Decision:
    """Create a new pending decision record before agents run."""
    decision = Decision(
        user_id=user_id,
        ticker=ticker.upper(),
        bull_thesis="",
        bear_thesis="",
        arbiter_reasoning="",
        bull_sources=[],
        bear_sources=[],
        market_context={},
        status="pending",
    )
    db.add(decision)
    await db.flush()
    await db.refresh(decision)
    return decision


# ── Read ───────────────────────────────────────────────────────────────────────

async def get_decision_by_id(
    db: AsyncSession,
    decision_id: uuid.UUID,
    *,
    load_signal: bool = True,
) -> Decision | None:
    q = select(Decision).where(Decision.id == decision_id)
    if load_signal:
        q = q.options(selectinload(Decision.signal))
    result = await db.execute(q)
    return result.scalar_one_or_none()


async def get_decisions_for_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    ticker: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Decision], int]:
    """Return paginated decisions and total count."""
    base = select(Decision).where(Decision.user_id == user_id)
    if ticker:
        base = base.where(Decision.ticker == ticker.upper())

    count_q = select(func.count()).select_from(base.subquery())
    total: int = (await db.execute(count_q)).scalar_one()

    data_q = (
        base.options(selectinload(Decision.signal))
        .order_by(desc(Decision.created_at))
        .offset(offset)
        .limit(limit)
    )
    rows = (await db.execute(data_q)).scalars().all()
    return list(rows), total


# ── Update ─────────────────────────────────────────────────────────────────────

async def update_decision_status(
    db: AsyncSession,
    decision_id: uuid.UUID,
    status: str,
    error_message: str | None = None,
) -> None:
    values: dict[str, Any] = {"status": status}
    if status == "complete":
        values["completed_at"] = datetime.now(UTC)
    if error_message is not None:
        values["error_message"] = error_message
    await db.execute(
        update(Decision).where(Decision.id == decision_id).values(**values)
    )


async def update_decision_content(
    db: AsyncSession,
    decision_id: uuid.UUID,
    *,
    bull_thesis: str,
    bear_thesis: str,
    arbiter_reasoning: str,
    bull_sources: list[dict[str, Any]],
    bear_sources: list[dict[str, Any]],
    market_context: dict[str, Any],
    embedding: list[float] | None = None,
) -> None:
    values: dict[str, Any] = {
        "bull_thesis": bull_thesis,
        "bear_thesis": bear_thesis,
        "arbiter_reasoning": arbiter_reasoning,
        "bull_sources": bull_sources,
        "bear_sources": bear_sources,
        "market_context": market_context,
        "status": "complete",
        "completed_at": datetime.now(UTC),
    }
    if embedding is not None:
        values["embedding"] = embedding
    await db.execute(
        update(Decision).where(Decision.id == decision_id).values(**values)
    )


# ── Vector Similarity Search ───────────────────────────────────────────────────

async def find_similar_decisions(
    db: AsyncSession,
    embedding: list[float],
    *,
    ticker: str | None = None,
    limit: int = 5,
    min_similarity: float = 0.75,
) -> list[tuple[Decision, float]]:
    """
    Cosine similarity search against past decisions.
    Returns (Decision, similarity_score) pairs sorted by relevance.
    Used by The Ear agent to surface historical context.
    """
    from pgvector.sqlalchemy import Vector

    similarity = (1 - Decision.embedding.cosine_distance(embedding)).label("similarity")

    q = (
        select(Decision, similarity)
        .where(Decision.embedding.is_not(None))
        .where(similarity >= min_similarity)
    )
    if ticker:
        q = q.where(Decision.ticker == ticker.upper())

    q = q.order_by(similarity.desc()).limit(limit)

    results = await db.execute(q)
    return [(row.Decision, row.similarity) for row in results]
