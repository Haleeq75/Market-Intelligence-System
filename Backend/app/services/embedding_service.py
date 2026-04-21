"""
app/services/embedding_service.py
───────────────────────────────────
Wraps the OpenAI embeddings API.
Returns a vector for any text string, used by The Ear agent
before pgvector similarity search.
"""
from __future__ import annotations

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)
_settings = get_settings()


class EmbeddingService:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=_settings.OPENAI_API_KEY)

    async def embed(self, text: str) -> list[float] | None:
        """
        Generate a vector embedding for the given text.
        Returns None on failure (pipeline continues without vector search).
        """
        if not text.strip():
            return None
        try:
            # Truncate to avoid token limit issues (embedding model limit: ~8k tokens)
            truncated = text[:12000]
            response = await self._client.embeddings.create(
                model=_settings.OPENAI_EMBEDDING_MODEL,
                input=truncated,
                dimensions=_settings.OPENAI_EMBEDDING_DIMENSIONS,
            )
            vector = response.data[0].embedding
            log.debug("embedding_generated", text_length=len(truncated), dimensions=len(vector))
            return vector
        except Exception as exc:
            log.error("embedding_failed", error=str(exc))
            return None

    async def embed_batch(self, texts: list[str]) -> list[list[float] | None]:
        """Embed multiple texts in a single API call."""
        if not texts:
            return []
        try:
            clean = [t[:12000] for t in texts if t.strip()]
            response = await self._client.embeddings.create(
                model=_settings.OPENAI_EMBEDDING_MODEL,
                input=clean,
                dimensions=_settings.OPENAI_EMBEDDING_DIMENSIONS,
            )
            return [item.embedding for item in response.data]
        except Exception as exc:
            log.error("batch_embedding_failed", error=str(exc))
            return [None] * len(texts)
