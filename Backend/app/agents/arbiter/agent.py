"""
app/agents/arbiter/agent.py
────────────────────────────
Arbiter Agent — weighs the Bull vs Bear debate, applies confidence
scoring rules, and emits the final BUY / HOLD / SELL verdict.
Persists the complete decision to the database.
"""
from __future__ import annotations

import json
import uuid

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.agents.arbiter.confidence import compute_verdict, reconcile_with_llm
from app.agents.prompts.arbiter import ARBITER_SYSTEM_PROMPT, ARBITER_TASK_TEMPLATE
from app.agents.state import FinalVerdict, SwarmState
from app.core.config import get_settings
from app.core.logging import get_logger
from app.database.session import async_session_factory

log = get_logger(__name__)
_settings = get_settings()


def _get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=_settings.OPENAI_MODEL,
        api_key=_settings.OPENAI_API_KEY,
        temperature=0.1,  # Low temp for decisive, consistent arbitration
        response_format={"type": "json_object"},
    )


async def arbiter_node(state: SwarmState) -> SwarmState:
    """
    LangGraph node: Arbiter.

    1. Calls LLM to weigh Bull vs Bear theses
    2. Applies rule-based confidence thresholds (safety override)
    3. Persists the full decision to PostgreSQL
    4. Returns final state with verdict
    """
    ticker = state["ticker"]
    decision_id = state["decision_id"]
    events = list(state.get("events", []))
    events.append(f"Arbiter: weighing Bull vs Bear for {ticker}")

    log.info("arbiter_node_start", ticker=ticker)
    await _update_status(decision_id, "running_arbiter")

    bull = state.get("bull_thesis")
    bear = state.get("bear_thesis")

    if not bull or not bear:
        err = "Missing bull or bear thesis — cannot arbitrate"
        log.error("arbiter_missing_theses", ticker=ticker)
        await _update_status(decision_id, "error", err)
        return {**state, "status": "error", "error": err, "events": events}

    try:
        llm = _get_llm()

        task_prompt = ARBITER_TASK_TEMPLATE.format(
            ticker=ticker,
            bull_confidence=bull["confidence"],
            bull_thesis=bull["thesis"],
            bull_key_points="\n".join(f"  • {p}" for p in bull.get("key_points", [])),
            bear_confidence=bear["confidence"],
            bear_thesis=bear["thesis"],
            bear_key_points="\n".join(f"  • {p}" for p in bear.get("key_points", [])),
            market_context=_format_market_context(state.get("market_context", {})),
            confidence_threshold=_settings.ARBITER_CONFIDENCE_THRESHOLD,
        )

        response = await llm.ainvoke([
            SystemMessage(content=ARBITER_SYSTEM_PROMPT),
            HumanMessage(content=task_prompt),
        ])

        raw = response.content
        data = json.loads(raw) if isinstance(raw, str) else raw

        # ── Apply rule-based confidence check ────────────────────────────────
        llm_bull_conf = float(data.get("bull_confidence", bull["confidence"]))
        llm_bear_conf = float(data.get("bear_confidence", bear["confidence"]))
        llm_signal = data.get("signal", "HOLD").upper()

        rule_result = compute_verdict(llm_bull_conf, llm_bear_conf)
        final_result = reconcile_with_llm(llm_signal, llm_bull_conf, llm_bear_conf, rule_result)

        reasoning = data.get("reasoning", "")
        if final_result.override_reason:
            reasoning += f"\n\n[RULE ENGINE]: {final_result.override_reason}"

        final_verdict = FinalVerdict(
            signal=final_result.signal,
            bull_confidence=final_result.bull_confidence,
            bear_confidence=final_result.bear_confidence,
            net_confidence=final_result.net_confidence,
            reasoning=reasoning,
            confidence_label=final_result.confidence_label,
        )

        events.append(
            f"Arbiter: verdict = {final_verdict['signal']} "
            f"(net confidence: {final_verdict['net_confidence']:.2f}, "
            f"{final_verdict['confidence_label']})"
        )
        log.info(
            "arbiter_node_complete",
            ticker=ticker,
            signal=final_verdict["signal"],
            net_confidence=final_verdict["net_confidence"],
        )

        # ── Persist full decision to database ─────────────────────────────────
        await _persist_decision(state, bull, bear, final_verdict)

        return {
            **state,
            "final_verdict": final_verdict,
            "status": "complete",
            "events": events,
            "error": None,
        }

    except Exception as exc:
        log.exception("arbiter_node_failed", ticker=ticker, error=str(exc))
        await _update_status(decision_id, "error", str(exc))
        return {**state, "status": "error", "error": str(exc), "events": events}


async def _persist_decision(
    state: SwarmState,
    bull: dict,
    bear: dict,
    verdict: FinalVerdict,
) -> None:
    """Write the complete decision record and trading signal to PostgreSQL."""
    from app.database.crud.decision import update_decision_content
    from app.database.crud.signal import create_signal
    from app.database.crud.asset import get_or_create_asset

    decision_id = uuid.UUID(state["decision_id"])
    user_id = uuid.UUID(state["user_id"])
    ticker = state["ticker"]

    async with async_session_factory() as db:
        try:
            # Update the decision record with full content
            await update_decision_content(
                db,
                decision_id,
                bull_thesis=bull["thesis"],
                bear_thesis=bear["thesis"],
                arbiter_reasoning=verdict["reasoning"],
                bull_sources=bull.get("sources_used", []),
                bear_sources=bear.get("sources_used", []),
                market_context=dict(state.get("market_context", {})),
                embedding=state.get("combined_embedding"),
            )

            # Get or create the asset record
            asset = await get_or_create_asset(db, user_id=user_id, ticker=ticker)

            # Write the trading signal
            await create_signal(
                db,
                asset_id=asset.id,
                decision_id=decision_id,
                signal=verdict["signal"],
                bull_confidence=verdict["bull_confidence"],
                bear_confidence=verdict["bear_confidence"],
                net_confidence=verdict["net_confidence"],
                price_at_signal=state.get("market_context", {}).get("price"),
            )

            await db.commit()
            log.info("decision_persisted", decision_id=str(decision_id))
        except Exception as exc:
            await db.rollback()
            log.error("decision_persist_failed", error=str(exc))
            raise


def _format_market_context(ctx: dict) -> str:
    if not ctx:
        return "No market data available."
    parts = []
    if ctx.get("price"):
        parts.append(f"Price: ${ctx['price']:,.2f}")
    if ctx.get("price_change_1d") is not None:
        parts.append(f"1d change: {ctx['price_change_1d']:+.2f}%")
    if ctx.get("pe_ratio"):
        parts.append(f"P/E: {ctx['pe_ratio']:.1f}")
    return " | ".join(parts) or "No context."


async def _update_status(decision_id: str, status: str, error: str | None = None) -> None:
    try:
        from app.database.crud.decision import update_decision_status
        async with async_session_factory() as db:
            await update_decision_status(db, uuid.UUID(decision_id), status, error)
            await db.commit()
    except Exception as e:
        log.warning("status_update_failed", error=str(e))
