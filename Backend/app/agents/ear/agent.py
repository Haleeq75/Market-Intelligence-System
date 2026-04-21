"""
app/agents/ear/agent.py
────────────────────────
"The Ear" — LangGraph node that ingests all external data,
embeds the context for pgvector search, and surfaces
similar historical decisions.
"""
from __future__ import annotations

import asyncio
import json
import uuid

from app.agents.ear.mcp_client import MCPClient
from app.agents.state import HistoricalDecision, SwarmState
from app.core.logging import get_logger
from app.database.crud.decision import find_similar_decisions
from app.database.session import async_session_factory
from app.services.embedding_service import EmbeddingService

log = get_logger(__name__)


async def ear_node(state: SwarmState) -> SwarmState:
    """
    LangGraph node: The Ear.

    Responsibilities:
    1. Fetch news, market context, and alternative data via MCPClient
    2. Embed the combined context text for semantic search
    3. Query pgvector to find similar historical decisions
    4. Update Decision DB record status to 'running_ear'
    5. Return enriched state for Bull + Bear agents
    """
    ticker = state["ticker"]
    decision_id = state["decision_id"]
    log.info("ear_node_start", ticker=ticker, decision_id=decision_id)

    events = list(state.get("events", []))
    events.append(f"Ear agent: ingesting data for {ticker}")

    # ── Update DB status ───────────────────────────────────────────────────────
    await _update_status(decision_id, "running_ear")

    try:
        async with MCPClient() as mcp:
            # Fan out all data fetches in parallel
            news_task = mcp.fetch_news(ticker)
            market_task = mcp.fetch_market_context(ticker)
            alt_task = mcp.fetch_alternative_data(ticker)

            news_articles, market_context, alternative_data = await asyncio.gather(
                news_task, market_task, alt_task
            )

        events.append(
            f"Ear agent: fetched {len(news_articles)} articles, "
            f"{len(alternative_data)} alt-data points"
        )
        log.info(
            "ear_node_data_fetched",
            ticker=ticker,
            news_count=len(news_articles),
            alt_data_count=len(alternative_data),
        )

        # ── Embed combined context ─────────────────────────────────────────────
        context_text = _build_context_text(ticker, news_articles, market_context, alternative_data)
        embedding_svc = EmbeddingService()
        embedding = await embedding_svc.embed(context_text)

        # ── Retrieve similar past decisions via pgvector ───────────────────────
        historical_decisions: list[HistoricalDecision] = []
        if embedding:
            async with async_session_factory() as db:
                similar = await find_similar_decisions(
                    db, embedding, ticker=ticker, limit=5, min_similarity=0.70
                )
                for decision, score in similar:
                    if decision.signal:
                        historical_decisions.append(
                            HistoricalDecision(
                                decision_id=str(decision.id),
                                ticker=decision.ticker,
                                signal=decision.signal.signal,
                                bull_confidence=float(decision.signal.bull_confidence),
                                bear_confidence=float(decision.signal.bear_confidence),
                                bull_thesis_snippet=decision.bull_thesis[:300],
                                similarity_score=round(score, 4),
                                created_at=decision.created_at.isoformat(),
                            )
                        )

        if historical_decisions:
            events.append(
                f"Ear agent: retrieved {len(historical_decisions)} similar past decisions"
            )

        return {
            **state,
            "news_articles": news_articles,
            "alternative_data": alternative_data,
            "market_context": market_context,
            "historical_decisions": historical_decisions,
            "combined_embedding": embedding,
            "status": "running_bull",
            "events": events,
            "error": None,
        }

    except Exception as exc:
        log.exception("ear_node_failed", ticker=ticker, error=str(exc))
        await _update_status(decision_id, "error", str(exc))
        return {**state, "status": "error", "error": str(exc), "events": events}


def _build_context_text(
    ticker: str,
    news: list,
    market: dict,
    alt_data: list,
) -> str:
    """Concatenate all context into a single text for embedding."""
    parts = [f"Asset: {ticker}"]
    if market.get("price"):
        parts.append(
            f"Price: ${market['price']} ({market.get('price_change_1d', 0):+.2f}% 1d)"
        )
    for article in news[:8]:
        parts.append(f"News: {article['title']} — {article['summary'][:200]}")
    for point in alt_data:
        parts.append(f"Alt data: {point['description']}")
    return "\n".join(parts)


async def _update_status(decision_id: str, status: str, error: str | None = None) -> None:
    try:
        from app.database.crud.decision import update_decision_status
        async with async_session_factory() as db:
            await update_decision_status(db, uuid.UUID(decision_id), status, error)
            await db.commit()
    except Exception as e:
        log.warning("status_update_failed", decision_id=decision_id, error=str(e))
