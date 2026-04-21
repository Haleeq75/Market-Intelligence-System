"""
app/database/models/decision.py
────────────────────────────────
DecisionJournal: the complete auditable record of every agent reasoning chain.
Includes a pgvector embedding for semantic similarity search across past decisions.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import get_settings
from app.database.session import Base

_settings = get_settings()


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ticker: Mapped[str] = mapped_column(Text, nullable=False, index=True)

    # ── Agent Outputs ────────────────────────────────────────────────────────
    # Raw thesis text from each agent
    bull_thesis: Mapped[str] = mapped_column(Text, nullable=False)
    bear_thesis: Mapped[str] = mapped_column(Text, nullable=False)
    arbiter_reasoning: Mapped[str] = mapped_column(Text, nullable=False)

    # Structured data (sources, key metrics, etc.)
    bull_sources: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    bear_sources: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    market_context: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    # ── Vector Embedding ─────────────────────────────────────────────────────
    # Semantic embedding of the combined bull+bear+arbiter text
    # Used for similarity search: "find past decisions similar to today's TSLA analysis"
    embedding: Mapped[list[float]] = mapped_column(
        Vector(_settings.OPENAI_EMBEDDING_DIMENSIONS), nullable=True
    )

    # ── Status ───────────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    # pending | running_ear | running_bull | running_bear | running_arbiter | complete | error
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship(back_populates="decisions", lazy="noload")  # noqa: F821
    signal: Mapped["TradingSignal | None"] = relationship(  # noqa: F821
        back_populates="decision", lazy="noload", uselist=False
    )

    # ── Indexes ───────────────────────────────────────────────────────────────
    __table_args__ = (
        # IVFFlat index for fast approximate nearest-neighbor search
        Index(
            "ix_decisions_embedding_ivfflat",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index("ix_decisions_ticker_created", "ticker", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Decision id={self.id} ticker={self.ticker} status={self.status}>"
