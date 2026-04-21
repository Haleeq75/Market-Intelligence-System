"""
app/services/notification_service.py
──────────────────────────────────────
WebSocket connection manager.
Allows any part of the system (agents, services) to push
real-time events to connected frontend clients.
"""
from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from typing import Any

from fastapi import WebSocket

from app.core.logging import get_logger

log = get_logger(__name__)


class ConnectionManager:
    """
    Manages active WebSocket connections, keyed by user_id.
    Each user can have multiple concurrent connections (tabs).
    """

    def __init__(self) -> None:
        # user_id → list of active WebSocket connections
        self._connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        self._connections[user_id].append(websocket)
        log.info("ws_connected", user_id=user_id, total=len(self._connections[user_id]))

    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        conns = self._connections.get(user_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self._connections.pop(user_id, None)
        log.info("ws_disconnected", user_id=user_id)

    async def send_to_user(self, user_id: str, event: dict[str, Any]) -> None:
        """Push a JSON event to all connections for a given user."""
        conns = self._connections.get(user_id, [])
        if not conns:
            return

        payload = json.dumps(event)
        dead: list[WebSocket] = []

        for ws in conns:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.disconnect(ws, user_id)

    async def broadcast_agent_event(
        self,
        user_id: str,
        decision_id: str,
        ticker: str,
        event_type: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """
        Broadcast a structured agent pipeline event.

        event_type values used by the frontend:
          agent_status  — agent started/completed a step
          final_signal  — Arbiter issued BUY/HOLD/SELL
          pipeline_error — something went wrong
        """
        await self.send_to_user(
            user_id,
            {
                "type": event_type,
                "decision_id": decision_id,
                "ticker": ticker,
                "message": message,
                "data": data or {},
            },
        )

    def active_user_count(self) -> int:
        return len(self._connections)


# Global singleton — imported by agents and API routers
ws_manager = ConnectionManager()


async def emit_agent_event(
    user_id: str,
    decision_id: str,
    ticker: str,
    event_type: str,
    message: str,
    data: dict[str, Any] | None = None,
) -> None:
    """Convenience wrapper for use inside agent nodes."""
    await ws_manager.broadcast_agent_event(
        user_id, decision_id, ticker, event_type, message, data
    )
