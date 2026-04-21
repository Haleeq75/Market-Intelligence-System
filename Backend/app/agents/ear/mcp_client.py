"""
app/agents/ear/mcp_client.py
─────────────────────────────
Async MCP (Model Context Protocol) client.
Connects to external data servers and normalises all responses
into the SwarmState typed structures.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.agents.state import AlternativeDataPoint, MarketContext, NewsArticle
from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)
_settings = get_settings()


class MCPClient:
    """
    Unified async client for all external data sources.
    Each method maps to a conceptual MCP server endpoint.
    In production these would be replaced by actual MCP server connections.
    """

    def __init__(self) -> None:
        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(15.0, connect=5.0),
            headers={"User-Agent": "AdversarialSwarm/1.0"},
        )

    async def __aenter__(self) -> "MCPClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self._http.aclose()

    # ── News ──────────────────────────────────────────────────────────────────

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def fetch_news(self, ticker: str, limit: int = 15) -> list[NewsArticle]:
        """Fetch and normalise news articles for a ticker via NewsAPI."""
        if not _settings.NEWS_API_KEY:
            log.warning("news_api_key_missing", ticker=ticker)
            return self._mock_news(ticker)

        try:
            resp = await self._http.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": ticker,
                    "sortBy": "publishedAt",
                    "pageSize": limit,
                    "language": "en",
                    "apiKey": _settings.NEWS_API_KEY,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            articles = data.get("articles", [])
            return [self._normalise_news_article(a) for a in articles]
        except httpx.HTTPError as e:
            log.error("news_fetch_failed", ticker=ticker, error=str(e))
            return self._mock_news(ticker)

    def _normalise_news_article(self, raw: dict[str, Any]) -> NewsArticle:
        return NewsArticle(
            title=raw.get("title") or "",
            source=(raw.get("source") or {}).get("name") or "Unknown",
            url=raw.get("url") or "",
            published_at=raw.get("publishedAt") or datetime.now(UTC).isoformat(),
            summary=raw.get("description") or raw.get("content") or "",
            sentiment=self._naive_sentiment(
                (raw.get("title") or "") + " " + (raw.get("description") or "")
            ),
            relevance=0.8,
        )

    # ── Market Data ───────────────────────────────────────────────────────────

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def fetch_market_context(self, ticker: str) -> MarketContext:
        """Fetch price + fundamentals via Finnhub."""
        if not _settings.FINNHUB_API_KEY:
            return self._mock_market_context(ticker)

        try:
            quote_task = self._http.get(
                "https://finnhub.io/api/v1/quote",
                params={"symbol": ticker, "token": _settings.FINNHUB_API_KEY},
            )
            profile_task = self._http.get(
                "https://finnhub.io/api/v1/stock/profile2",
                params={"symbol": ticker, "token": _settings.FINNHUB_API_KEY},
            )
            quote_resp, profile_resp = await asyncio.gather(quote_task, profile_task)
            quote_resp.raise_for_status()
            profile_resp.raise_for_status()

            q = quote_resp.json()
            p = profile_resp.json()

            return MarketContext(
                price=q.get("c"),
                price_change_1d=round(((q.get("c", 0) - q.get("pc", 1)) / max(q.get("pc", 1), 0.01)) * 100, 2),
                price_change_5d=None,
                volume=q.get("v"),
                market_cap=p.get("marketCapitalization"),
                pe_ratio=None,
                fifty_two_week_high=q.get("h"),
                fifty_two_week_low=q.get("l"),
                currency="USD",
            )
        except httpx.HTTPError as e:
            log.error("market_fetch_failed", ticker=ticker, error=str(e))
            return self._mock_market_context(ticker)

    # ── Alternative Data ──────────────────────────────────────────────────────

    async def fetch_alternative_data(self, ticker: str) -> list[AlternativeDataPoint]:
        """
        Aggregate alternative data signals.
        In production: connects to dedicated MCP servers for
        Reddit sentiment, web traffic, options flow, etc.
        """
        tasks = [
            self._fetch_reddit_sentiment(ticker),
            self._fetch_google_trends(ticker),
            self._fetch_options_flow(ticker),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        points: list[AlternativeDataPoint] = []
        for r in results:
            if isinstance(r, list):
                points.extend(r)
            elif isinstance(r, Exception):
                log.warning("alt_data_source_failed", error=str(r))
        return points

    async def _fetch_reddit_sentiment(self, ticker: str) -> list[AlternativeDataPoint]:
        # Production: connect to Reddit MCP server
        return [
            AlternativeDataPoint(
                source="reddit",
                category="social_sentiment",
                value=0.62,
                description=f"r/wallstreetbets and r/stocks mention ratio for {ticker} is elevated (62% bullish over 24h)",
                timestamp=datetime.now(UTC).isoformat(),
            )
        ]

    async def _fetch_google_trends(self, ticker: str) -> list[AlternativeDataPoint]:
        return [
            AlternativeDataPoint(
                source="google_trends",
                category="web_engagement",
                value=0.71,
                description=f"Search interest for '{ticker}' is 71/100 (above 30-day average of 58)",
                timestamp=datetime.now(UTC).isoformat(),
            )
        ]

    async def _fetch_options_flow(self, ticker: str) -> list[AlternativeDataPoint]:
        return [
            AlternativeDataPoint(
                source="options_flow",
                category="derivatives_sentiment",
                value=0.55,
                description=f"Put/call ratio for {ticker} is 0.72 (below 1.0 → net bullish options positioning)",
                timestamp=datetime.now(UTC).isoformat(),
            )
        ]

    # ── Utilities / Mocks ─────────────────────────────────────────────────────

    def _naive_sentiment(self, text: str) -> float:
        """Lexicon-based sentiment placeholder. Replace with model in production."""
        bull_words = {"surge", "beat", "record", "growth", "strong", "raised", "upgrade", "buy"}
        bear_words = {"miss", "drop", "loss", "decline", "weak", "cut", "downgrade", "sell", "risk"}
        tokens = set(text.lower().split())
        bull_hits = len(tokens & bull_words)
        bear_hits = len(tokens & bear_words)
        total = bull_hits + bear_hits
        if total == 0:
            return 0.0
        return round((bull_hits - bear_hits) / total, 2)

    def _mock_news(self, ticker: str) -> list[NewsArticle]:
        return [
            NewsArticle(
                title=f"{ticker} Reports Strong Quarterly Earnings Beat",
                source="Mock Financial Times",
                url=f"https://example.com/{ticker.lower()}-earnings",
                published_at=datetime.now(UTC).isoformat(),
                summary=f"{ticker} exceeded analyst expectations with revenue up 18% YoY.",
                sentiment=0.7,
                relevance=0.9,
            ),
            NewsArticle(
                title=f"Analysts Raise Price Target for {ticker}",
                source="Mock Bloomberg",
                url=f"https://example.com/{ticker.lower()}-pt",
                published_at=datetime.now(UTC).isoformat(),
                summary="Three major banks raised their 12-month price targets citing margin expansion.",
                sentiment=0.65,
                relevance=0.85,
            ),
        ]

    def _mock_market_context(self, ticker: str) -> MarketContext:
        return MarketContext(
            price=185.50,
            price_change_1d=2.3,
            price_change_5d=-1.1,
            volume=45_000_000,
            market_cap=580_000,
            pe_ratio=28.5,
            fifty_two_week_high=220.00,
            fifty_two_week_low=140.00,
            currency="USD",
        )
