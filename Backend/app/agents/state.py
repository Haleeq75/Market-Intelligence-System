"""
app/agents/state.py
────────────────────
SwarmState: the single shared TypedDict that flows through every
LangGraph node in the adversarial swarm pipeline.

Every agent reads from and writes to this state.
LangGraph manages the immutable state transitions.
"""
from __future__ import annotations

import uuid
from typing import Any, TypedDict


class NewsArticle(TypedDict):
    title: str
    source: str
    url: str
    published_at: str
    summary: str
    sentiment: float  # -1.0 (very bearish) to +1.0 (very bullish)
    relevance: float  # 0.0 to 1.0


class AlternativeDataPoint(TypedDict):
    source: str           # "reddit", "twitter", "satellite", "web_traffic"
    category: str         # "social_sentiment", "physical_activity", "web_engagement"
    value: float          # normalised signal value
    description: str
    timestamp: str


class MarketContext(TypedDict):
    price: float | None
    price_change_1d: float | None   # %
    price_change_5d: float | None   # %
    volume: float | None
    market_cap: float | None
    pe_ratio: float | None
    fifty_two_week_high: float | None
    fifty_two_week_low: float | None
    currency: str


class HistoricalDecision(TypedDict):
    decision_id: str
    ticker: str
    signal: str
    bull_confidence: float
    bear_confidence: float
    bull_thesis_snippet: str
    similarity_score: float
    created_at: str


class AgentThesis(TypedDict):
    thesis: str                        # Full reasoning text
    key_points: list[str]              # 3-5 bullet points
    confidence: float                  # 0.0 to 1.0
    sources_used: list[NewsArticle | dict[str, Any]]
    agent: str                         # "bull" | "bear"


class FinalVerdict(TypedDict):
    signal: str                        # "BUY" | "HOLD" | "SELL"
    bull_confidence: float
    bear_confidence: float
    net_confidence: float              # abs(bull - bear) — how decisive the call is
    reasoning: str                     # Arbiter's full reasoning chain
    confidence_label: str             # "HIGH" | "MEDIUM" | "LOW"


class SwarmState(TypedDict):
    # ── Inputs ───────────────────────────────────────────────────────────────
    decision_id: str                   # UUID of the Decision DB record
    user_id: str                       # UUID of requesting user
    ticker: str                        # e.g. "TSLA"

    # ── Ear Agent outputs ─────────────────────────────────────────────────────
    news_articles: list[NewsArticle]
    alternative_data: list[AlternativeDataPoint]
    market_context: MarketContext
    historical_decisions: list[HistoricalDecision]  # Similar past decisions from pgvector
    combined_embedding: list[float] | None          # Embedding for this analysis session

    # ── Bull / Bear outputs ───────────────────────────────────────────────────
    bull_thesis: AgentThesis | None
    bear_thesis: AgentThesis | None

    # ── Arbiter output ────────────────────────────────────────────────────────
    final_verdict: FinalVerdict | None

    # ── Pipeline control ──────────────────────────────────────────────────────
    status: str                        # mirrors Decision.status
    error: str | None
    events: list[str]                  # Append-only log of pipeline events (for WS streaming)
