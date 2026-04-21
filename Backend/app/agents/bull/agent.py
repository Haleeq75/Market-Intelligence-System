"""
app/agents/bull/agent.py
─────────────────────────
Bull Agent — constructs the strongest possible bullish thesis
using the data surfaced by The Ear.
"""
from __future__ import annotations

import json
import uuid

from langchain_openai import ChatOpenAI

from app.agents.prompts.bull import BULL_SYSTEM_PROMPT, BULL_TASK_TEMPLATE
from app.agents.state import AgentThesis, SwarmState
from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)
_settings = get_settings()


def _get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=_settings.OPENAI_MODEL,
        api_key=_settings.OPENAI_API_KEY,
        temperature=0.3,
        response_format={"type": "json_object"},
    )


async def bull_node(state: SwarmState) -> SwarmState:
    """
    LangGraph node: Bull Agent.

    Receives the enriched state from The Ear and builds a bullish thesis.
    Returns state with bull_thesis populated.
    """
    ticker = state["ticker"]
    decision_id = state["decision_id"]
    events = list(state.get("events", []))
    events.append(f"Bull agent: constructing bullish thesis for {ticker}")

    log.info("bull_node_start", ticker=ticker)
    await _update_status(decision_id, "running_bull")

    try:
        llm = _get_llm()

        task_prompt = BULL_TASK_TEMPLATE.format(
            ticker=ticker,
            market_context=_format_market_context(state.get("market_context", {})),
            news_count=len(state.get("news_articles", [])),
            news_articles=_format_news(state.get("news_articles", [])),
            alternative_data=_format_alt_data(state.get("alternative_data", [])),
            historical_decisions=_format_history(state.get("historical_decisions", [])),
        )

        from langchain_core.messages import HumanMessage, SystemMessage
        response = await llm.ainvoke([
            SystemMessage(content=BULL_SYSTEM_PROMPT),
            HumanMessage(content=task_prompt),
        ])

        raw = response.content
        data = json.loads(raw) if isinstance(raw, str) else raw

        bull_thesis = AgentThesis(
            thesis=data.get("thesis", ""),
            key_points=data.get("key_points", []),
            confidence=float(data.get("confidence", 0.5)),
            sources_used=data.get("sources_used", []),
            agent="bull",
        )

        events.append(
            f"Bull agent: thesis complete — confidence {bull_thesis['confidence']:.2f}"
        )
        log.info(
            "bull_node_complete",
            ticker=ticker,
            confidence=bull_thesis["confidence"],
        )

        return {
            **state,
            "bull_thesis": bull_thesis,
            "status": "running_bear",
            "events": events,
        }

    except Exception as exc:
        log.exception("bull_node_failed", ticker=ticker, error=str(exc))
        # Fallback thesis to allow pipeline to continue
        fallback = AgentThesis(
            thesis=f"Bull analysis failed for {ticker}: {exc}",
            key_points=["Analysis unavailable"],
            confidence=0.0,
            sources_used=[],
            agent="bull",
        )
        return {**state, "bull_thesis": fallback, "status": "running_bear", "events": events}


# ── Formatting helpers ────────────────────────────────────────────────────────

def _format_market_context(ctx: dict) -> str:
    if not ctx:
        return "No market data available."
    lines = []
    if ctx.get("price"):
        lines.append(f"Current price: ${ctx['price']:,.2f} {ctx.get('currency', 'USD')}")
    if ctx.get("price_change_1d") is not None:
        lines.append(f"1-day change: {ctx['price_change_1d']:+.2f}%")
    if ctx.get("market_cap"):
        lines.append(f"Market cap: ${ctx['market_cap']:,.0f}M")
    if ctx.get("pe_ratio"):
        lines.append(f"P/E ratio: {ctx['pe_ratio']:.1f}")
    if ctx.get("fifty_two_week_high"):
        lines.append(
            f"52-week range: ${ctx.get('fifty_two_week_low', 0):.2f} – ${ctx['fifty_two_week_high']:.2f}"
        )
    return "\n".join(lines) or "No market data available."


def _format_news(articles: list) -> str:
    if not articles:
        return "No news articles available."
    return "\n\n".join(
        f"[{i+1}] {a['title']}\nSource: {a['source']} | Sentiment: {a['sentiment']:+.2f}\n{a['summary']}"
        for i, a in enumerate(articles[:10])
    )


def _format_alt_data(points: list) -> str:
    if not points:
        return "No alternative data available."
    return "\n".join(
        f"• [{p['source'].upper()}] {p['description']} (signal: {p['value']:.2f})"
        for p in points
    )


def _format_history(history: list) -> str:
    if not history:
        return "No similar historical decisions found."
    return "\n".join(
        f"• {h['created_at'][:10]} | Signal: {h['signal']} | "
        f"Bull: {h['bull_confidence']:.2f} | Bear: {h['bear_confidence']:.2f} | "
        f"Similarity: {h['similarity_score']:.2f}\n  Snippet: {h['bull_thesis_snippet'][:150]}..."
        for h in history
    )


async def _update_status(decision_id: str, status: str) -> None:
    try:
        from app.database.crud.decision import update_decision_status
        from app.database.session import async_session_factory
        async with async_session_factory() as db:
            await update_decision_status(db, uuid.UUID(decision_id), status)
            await db.commit()
    except Exception as e:
        log.warning("status_update_failed", error=str(e))
