"""
CollateralOps — WebSocket real-time updates (T28).
Push live score changes, new proofs, and asset updates to connected dashboards.
"""
import asyncio
import json
from typing import Set

from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    def __init__(self):
        self.active: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active.discard(websocket)

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        dead = set()
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        self.active -= dead


manager = ConnectionManager()


async def websocket_handler(websocket: WebSocket):
    """Handle WebSocket connections for live dashboard updates."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            # Echo back or handle subscription commands
            if msg.get("action") == "subscribe":
                await websocket.send_json({"type": "subscribed", "channel": msg.get("channel", "all")})
            elif msg.get("action") == "ping":
                await websocket.send_json({"type": "pong", "ts": msg.get("ts")})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def notify_asset_update(asset_id: str, asset_name: str, change_type: str, payload: dict):
    """Notify all clients about an asset update."""
    await manager.broadcast({
        "type": "asset_update",
        "asset_id": asset_id,
        "asset_name": asset_name,
        "change_type": change_type,
        "payload": payload,
    })


async def notify_new_proof(asset_id: str, proof_id: str, event_type: str):
    """Notify when a new proof event is added."""
    await manager.broadcast({
        "type": "new_proof",
        "asset_id": asset_id,
        "proof_id": proof_id,
        "event_type": event_type,
    })


async def notify_score_change(asset_id: str, old_score: float, new_score: float):
    """Notify when a financeability score changes."""
    await manager.broadcast({
        "type": "score_change",
        "asset_id": asset_id,
        "old_score": old_score,
        "new_score": new_score,
        "delta": round(new_score - old_score, 1),
    })
