"""
app/database/models/signal.py
───────────────────────────────
TradingSignal: the final Buy/Hold/Sell verdict emitted by the Arbiter.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class TradingSignal(Base):
    __tablename__ = "trading_signals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    decision_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("decisions.id", ondelete="CASCADE"), nullable=False
    )

    # Signal fields
    signal: Mapped[str] = mapped_column(String(10), nullable=False)  # BUY | HOLD | SELL
    bull_confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    bear_confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    net_confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)

    # Price context at time of signal
    price_at_signal: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )

    # Relationships
    asset: Mapped["Asset"] = relationship(back_populates="signals", lazy="noload")  # noqa: F821
    decision: Mapped["Decision"] = relationship(back_populates="signal", lazy="noload")  # noqa: F821

    def __repr__(self) -> str:
        return f"<TradingSignal {self.signal} net={self.net_confidence}>"
