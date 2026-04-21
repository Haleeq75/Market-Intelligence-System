"""
app/services/analysis_service.py
──────────────────────────────────
Bridges the FastAPI layer with the LangGraph swarm.
Handles background task execution and real-time event broadcasting.
"""
from __future__ import annotations

import asyncio
import uuid

from app.agents.graph import get_compiled_graph
from app.agents.state import SwarmState
from app.core.logging import get_logger
from app.database.crud.decision import create_decision
from app.database.session import async_session_factory
from app.services.notification_service import emit_agent_event

log = get_logger(__name__)


async def run_swarm_analysis(
    *,
    user_id: uuid.UUID,
    ticker: str,
) -> uuid.UUID:
    """
    Kick off the full adversarial swarm pipeline for a given asset.

    1. Creates a pending Decision record in the DB
    2. Fires the LangGraph graph as a background asyncio task
    3. Returns the decision_id immediately (non-blocking)

    The frontend receives real-time progress via WebSocket.
    """
    ticker = ticker.upper().strip()

    # Create the decision record upfront so the frontend can track it
    async with async_session_factory() as db:
        decision = await create_decision(db, user_id=user_id, ticker=ticker)
        await db.commit()
        decision_id = decision.id

    log.info(
        "analysis_queued",
        user_id=str(user_id),
        ticker=ticker,
        decision_id=str(decision_id),
    )

    # Fire and forget — runs in background
    asyncio.create_task(
        _execute_pipeline(
            user_id=str(user_id),
            ticker=ticker,
            decision_id=str(decision_id),
        )
    )

    return decision_id


async def _execute_pipeline(
    *,
    user_id: str,
    ticker: str,
    decision_id: str,
) -> None:
    """
    Executes the LangGraph pipeline and streams progress events
    to the user's WebSocket connection.
    """
    log.info("pipeline_start", ticker=ticker, decision_id=decision_id)

    await emit_agent_event(
        user_id, decision_id, ticker,
        "agent_status",
        f"Starting analysis for {ticker}",
        {"status": "pending"},
    )

    initial_state = SwarmState(
        decision_id=decision_id,
        user_id=user_id,
        ticker=ticker,
        news_articles=[],
        alternative_data=[],
        market_context={},  # type: ignore[typeddict-item]
        historical_decisions=[],
        combined_embedding=None,
        bull_thesis=None,
        bear_thesis=None,
        final_verdict=None,
        status="pending",
        error=None,
        events=[],
    )

    try:
        graph = get_compiled_graph()
        final_state: SwarmState = await graph.ainvoke(initial_state)

        # Broadcast each pipeline event that was collected
        for event_msg in final_state.get("events", []):
            await emit_agent_event(
                user_id, decision_id, ticker, "agent_status", event_msg
            )
            await asyncio.sleep(0.05)  # brief stagger for UX

        # Broadcast the final verdict
        if final_state.get("final_verdict"):
            v = final_state["final_verdict"]
            await emit_agent_event(
                user_id, decision_id, ticker,
                "final_signal",
                f"Analysis complete: {v['signal']}",
                {
                    "signal": v["signal"],
                    "bull_confidence": v["bull_confidence"],
                    "bear_confidence": v["bear_confidence"],
                    "net_confidence": v["net_confidence"],
                    "confidence_label": v["confidence_label"],
                    "decision_id": decision_id,
                },
            )
        elif final_state.get("status") == "error":
            await emit_agent_event(
                user_id, decision_id, ticker,
                "pipeline_error",
                f"Analysis failed: {final_state.get('error', 'Unknown error')}",
            )

        log.info(
            "pipeline_complete",
            ticker=ticker,
            decision_id=decision_id,
            status=final_state.get("status"),
        )

    except Exception as exc:
        log.exception("pipeline_crashed", ticker=ticker, decision_id=decision_id, error=str(exc))
        await emit_agent_event(
            user_id, decision_id, ticker,
            "pipeline_error",
            f"Pipeline crashed: {exc}",
        )
