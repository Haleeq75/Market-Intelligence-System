"""
app/api/v1/analysis.py — POST /analysis/run
"""
from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException

analysis_router = APIRouter(prefix="/analysis", tags=["analysis"])


@analysis_router.post("/run", status_code=202)
async def run_analysis(
    body: "AnalysisRequest",
    db: "DbSession",
    current_user: "CurrentUser",
):
    from app.api.schemas.all import AnalysisRequest, AnalysisStartedResponse
    from app.services.analysis_service import run_swarm_analysis
    decision_id = await run_swarm_analysis(
        user_id=current_user.id,
        ticker=body.ticker,
    )
    return AnalysisStartedResponse(
        decision_id=decision_id,
        ticker=body.ticker,
        status="pending",
    )


@analysis_router.get("/status/{decision_id}")
async def get_analysis_status(decision_id: UUID, db: "DbSession", current_user: "CurrentUser"):
    from app.database.crud.decision import get_decision_by_id
    decision = await get_decision_by_id(db, decision_id)
    if not decision or str(decision.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Decision not found")
    return {"decision_id": decision_id, "status": decision.status, "ticker": decision.ticker}
