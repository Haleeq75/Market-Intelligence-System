"""
app/api/v1/signals.py — TradingSignal endpoints
"""
from __future__ import annotations
from fastapi import APIRouter, Query

signals_router = APIRouter(prefix="/signals", tags=["signals"])


@signals_router.get("")
async def get_signals(
    db: "DbSession",
    current_user: "CurrentUser",
    ticker: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    from app.database.crud.signal import get_latest_signals
    from app.api.schemas.all import SignalResponse
    signals = await get_latest_signals(db, current_user.id, ticker=ticker, limit=limit)
    return [
        SignalResponse(
            id=s.id,
            ticker=s.asset.ticker,
            signal=s.signal,
            bull_confidence=s.bull_confidence,
            bear_confidence=s.bear_confidence,
            net_confidence=s.net_confidence,
            price_at_signal=s.price_at_signal,
            currency=s.currency,
            created_at=s.created_at,
        )
        for s in signals
    ]


"""
app/api/v1/assets.py — Asset watchlist endpoints
"""
from fastapi import APIRouter, HTTPException

assets_router = APIRouter(prefix="/assets", tags=["assets"])


@assets_router.get("")
async def list_assets(db: "DbSession", current_user: "CurrentUser"):
    from app.database.crud.asset import get_assets_for_user
    from app.api.schemas.all import AssetResponse
    assets = await get_assets_for_user(db, current_user.id)
    return [AssetResponse.model_validate(a) for a in assets]


@assets_router.post("", status_code=201)
async def add_asset(body: "AssetCreateRequest", db: "DbSession", current_user: "CurrentUser"):
    from app.database.crud.asset import create_asset
    from app.api.schemas.all import AssetResponse
    asset = await create_asset(
        db, user_id=current_user.id,
        ticker=body.ticker, name=body.name, asset_class=body.asset_class,
    )
    return AssetResponse.model_validate(asset)


@assets_router.delete("/{asset_id}", status_code=204)
async def delete_asset(asset_id: "UUID", db: "DbSession", current_user: "CurrentUser"):
    from app.database.crud.asset import delete_asset as _delete
    deleted = await _delete(db, asset_id=asset_id, user_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Asset not found")
