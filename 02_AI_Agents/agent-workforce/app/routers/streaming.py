import json
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.agents.all_agents import AGENT_REGISTRY
from app.core.logging import get_logger

router = APIRouter(prefix="/ws", tags=["streaming"])
logger = get_logger("websocket")

# Active connections per agent
agent_connections: dict[str, Set[WebSocket]] = {}


@router.websocket("/{agent_id}")
async def agent_websocket(websocket: WebSocket, agent_id: str):
    """WebSocket for real-time agent execution streaming."""
    if agent_id not in AGENT_REGISTRY:
        await websocket.close(code=4004, reason="Agent not found")
        return

    await websocket.accept()
    agent_connections.setdefault(agent_id, set()).add(websocket)
    agent = AGENT_REGISTRY[agent_id]

    await websocket.send_json({
        "type": "connected",
        "agent_id": agent_id,
        "agent_name": agent.name,
        "message": f"Connected to {agent.name}. Send a JSON with 'query' to run.",
    })

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            query = payload.get("query", "")
            context = payload.get("context", {})
            if not query:
                await websocket.send_json({"type": "error", "message": "Missing 'query' field"})
                continue

            from app.models.schemas import AgentRequest
            request = AgentRequest(query=query, context=context)

            # Stream start
            await websocket.send_json({
                "type": "run_started",
                "agent_id": agent_id,
                "query": query[:200],
            })

            # Execute
            try:
                result = await agent.run(request)
                await websocket.send_json({
                    "type": "run_complete",
                    "agent_id": agent_id,
                    "status": result.status,
                    "output": result.output if isinstance(result.output, dict) else {"text": str(result.output)},
                    "tokens_used": result.tokens_used,
                    "cost": result.cost,
                    "duration_ms": result.duration_ms,
                })
            except Exception as exc:
                await websocket.send_json({
                    "type": "run_error",
                    "agent_id": agent_id,
                    "error": str(exc),
                })

    except WebSocketDisconnect:
        agent_connections[agent_id].discard(websocket)
    except Exception as exc:
        logger.error("websocket_error", agent_id=agent_id, error=str(exc))
        agent_connections[agent_id].discard(websocket)


@router.websocket("/")
async def global_websocket(websocket: WebSocket):
    """Global WebSocket for portfolio-wide updates."""
    await websocket.accept()
    await websocket.send_json({
        "type": "connected",
        "message": "Connected to Agent Workforce global stream.",
        "agents_available": list(AGENT_REGISTRY.keys()),
    })
    try:
        while True:
            raw = await websocket.receive_text()
            await websocket.send_json({
                "type": "pong",
                "agents_count": len(AGENT_REGISTRY),
            })
    except WebSocketDisconnect:
        pass
