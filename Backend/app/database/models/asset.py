"""
app/database/models/asset.py
──────────────────────────────
Asset (ticker) watchlist model.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Asset(Base):
    __tablename__ = "assets"
    __table_args__ = (
        UniqueConstraint("user_id", "ticker", name="uq_asset_user_ticker"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    asset_class: Mapped[str] = mapped_column(
        String(50), nullable=False, default="equity"
    )  # equity | crypto | forex | commodity
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="watchlist", lazy="noload")  # noqa: F821
    signals: Mapped[list["TradingSignal"]] = relationship(  # noqa: F821
        back_populates="asset", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<Asset {self.ticker} ({self.asset_class})>"
