"""
app/api/v1/ws.py
─────────────────
WebSocket endpoint for real-time agent status streaming.
The frontend connects here and receives all pipeline events
as JSON messages over a persistent connection.
"""
from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger
from app.core.security import validate_access_token
from app.services.notification_service import ws_manager

log = get_logger(__name__)
ws_router = APIRouter(tags=["websocket"])


@ws_router.websocket("/ws/live")
async def websocket_live(websocket: WebSocket, token: str):
    """
    WebSocket connection endpoint.

    Authentication: pass JWT as query param ?token=<access_token>
    Example: ws://localhost:8000/ws/live?token=eyJ...

    The connection stays open and receives events:
    {
        "type": "agent_status" | "final_signal" | "pipeline_error",
        "decision_id": "...",
        "ticker": "TSLA",
        "message": "Bull agent: thesis complete — confidence 0.72",
        "data": { ... }
    }
    """
    # Authenticate before accepting
    try:
        user_id = validate_access_token(token)
    except Exception:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await ws_manager.connect(websocket, user_id)
    log.info("ws_session_started", user_id=user_id)

    try:
        # Send a connection confirmation
        import json
        await websocket.send_text(json.dumps({
            "type": "connected",
            "message": "Connected to Adversarial Swarm live feed",
        }))

        # Keep connection alive — wait for client disconnect or ping
        while True:
            try:
                data = await websocket.receive_text()
                # Handle ping/pong keepalive from client
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(websocket, user_id)
        log.info("ws_session_ended", user_id=user_id)
