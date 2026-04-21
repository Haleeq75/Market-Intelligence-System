"""
app/api/v1/journal.py — Decision Journal endpoints
"""
from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query

journal_router = APIRouter(prefix="/journal", tags=["journal"])


@journal_router.get("")
async def list_decisions(
    db: "DbSession",
    current_user: "CurrentUser",
    ticker: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    from app.database.crud.decision import get_decisions_for_user
    from app.api.schemas.all import DecisionSummaryResponse, PaginatedResponse
    decisions, total = await get_decisions_for_user(
        db, current_user.id,
        ticker=ticker,
        offset=(page - 1) * page_size,
        limit=page_size,
    )
    items = []
    for d in decisions:
        item = DecisionSummaryResponse(
            id=d.id, ticker=d.ticker, status=d.status,
            signal=d.signal.signal if d.signal else None,
            bull_confidence=d.signal.bull_confidence if d.signal else None,
            bear_confidence=d.signal.bear_confidence if d.signal else None,
            net_confidence=d.signal.net_confidence if d.signal else None,
            confidence_label=None,
            created_at=d.created_at, completed_at=d.completed_at,
        )
        items.append(item)
    import math
    return PaginatedResponse[DecisionSummaryResponse](
        items=items, total=total, page=page, page_size=page_size,
        pages=math.ceil(total / page_size),
    )


@journal_router.get("/{decision_id}")
async def get_decision(decision_id: UUID, db: "DbSession", current_user: "CurrentUser"):
    from app.database.crud.decision import get_decision_by_id
    from app.api.schemas.all import DecisionDetailResponse
    d = await get_decision_by_id(db, decision_id, load_signal=True)
    if not d or str(d.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Decision not found")
    return DecisionDetailResponse(
        id=d.id, ticker=d.ticker, status=d.status, error_message=d.error_message,
        bull_thesis=d.bull_thesis, bear_thesis=d.bear_thesis,
        arbiter_reasoning=d.arbiter_reasoning,
        bull_sources=d.bull_sources, bear_sources=d.bear_sources,
        market_context=d.market_context,
        signal=d.signal.signal if d.signal else None,
        bull_confidence=d.signal.bull_confidence if d.signal else None,
        bear_confidence=d.signal.bear_confidence if d.signal else None,
        net_confidence=d.signal.net_confidence if d.signal else None,
        price_at_signal=d.signal.price_at_signal if d.signal else None,
        created_at=d.created_at, completed_at=d.completed_at,
    )
