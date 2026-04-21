"""
app/api/schemas/
─────────────────
All Pydantic v2 request/response schemas for the API layer.
Intentionally separate from ORM models (no SQLAlchemy coupling).
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# ═══════════════════════════════════════════════════════════════════════════════
# Auth schemas
# ═══════════════════════════════════════════════════════════════════════════════

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# ═══════════════════════════════════════════════════════════════════════════════
# Asset schemas
# ═══════════════════════════════════════════════════════════════════════════════

class AssetCreateRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=20)
    name: str | None = None
    asset_class: str = Field(default="equity", pattern="^(equity|crypto|forex|commodity)$")

    @field_validator("ticker")
    @classmethod
    def uppercase_ticker(cls, v: str) -> str:
        return v.upper().strip()


class AssetResponse(BaseModel):
    id: UUID
    ticker: str
    name: str | None
    asset_class: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════════════
# Analysis schemas
# ═══════════════════════════════════════════════════════════════════════════════

class AnalysisRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=20)

    @field_validator("ticker")
    @classmethod
    def uppercase_ticker(cls, v: str) -> str:
        return v.upper().strip()


class AnalysisStartedResponse(BaseModel):
    decision_id: UUID
    ticker: str
    status: str = "pending"
    message: str = "Analysis queued. Connect to WebSocket for live updates."


# ═══════════════════════════════════════════════════════════════════════════════
# Signal schemas
# ═══════════════════════════════════════════════════════════════════════════════

class SignalResponse(BaseModel):
    id: UUID
    ticker: str
    signal: str                     # BUY | HOLD | SELL
    bull_confidence: Decimal
    bear_confidence: Decimal
    net_confidence: Decimal
    price_at_signal: Decimal | None
    currency: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════════════
# Decision Journal schemas
# ═══════════════════════════════════════════════════════════════════════════════

class SourceCitation(BaseModel):
    title: str
    source: str
    url: str | None = None
    relevance: str | None = None
    sentiment: float | None = None


class DecisionSummaryResponse(BaseModel):
    """Lightweight card for the journal list view."""
    id: UUID
    ticker: str
    status: str
    signal: str | None = None
    bull_confidence: Decimal | None = None
    bear_confidence: Decimal | None = None
    net_confidence: Decimal | None = None
    confidence_label: str | None = None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class DecisionDetailResponse(BaseModel):
    """Full decision for the deep-dive journal view."""
    id: UUID
    ticker: str
    status: str
    error_message: str | None

    # Agent outputs
    bull_thesis: str
    bear_thesis: str
    arbiter_reasoning: str
    bull_sources: list[dict[str, Any]]
    bear_sources: list[dict[str, Any]]
    market_context: dict[str, Any]

    # Signal (if complete)
    signal: str | None = None
    bull_confidence: Decimal | None = None
    bear_confidence: Decimal | None = None
    net_confidence: Decimal | None = None
    price_at_signal: Decimal | None = None

    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════════════
# Paginated response wrapper
# ═══════════════════════════════════════════════════════════════════════════════

class PaginatedResponse[T](BaseModel):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int
