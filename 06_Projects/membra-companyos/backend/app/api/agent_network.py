"""MEMBRA Agent Network Protocol OS API — 60 Autonomous LLM Agents.
Each agent is a dot-notation identity: {name}.{department}.membra
"""
import asyncio
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()

# Lazy-load registry so agents are only instantiated on first request
_registry = None


def _get_registry():
    global _registry
    if _registry is None:
        import os
        from app.agents.registry import AgentRegistry
        _registry = AgentRegistry(
            ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            mode=os.getenv("AGENT_MODE", "local"),
        )
        asyncio.get_event_loop().run_until_complete(_registry.load_all())
    return _registry


class RunRequest(BaseModel):
    prompt: str
    context: Optional[str] = None


class MessageRequest(BaseModel):
    dst: str  # target agent_id
    msg_type: str = "rpc"
    payload: Dict[str, Any] = {}


# ─── Registry ───
@router.post("/network/load")
async def load_agents():
    reg = _get_registry()
    return {"loaded": len(reg.list_all()), "status": "ok"}


@router.get("/network/agents")
def list_agents(
    department: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    reg = _get_registry()
    agents = reg.list_all()
    if department:
        agents = [a for a in agents if a["department"] == department]
    if status:
        agents = [a for a in agents if a["status"] == status]
    if search:
        agents = [a for a in agents if search.lower() in a["full_name"] or search.lower() in a["title"]]
    total = len(agents)
    agents = agents[offset:offset + limit]
    return {
        "items": agents,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/network/agents/{agent_id}")
def get_agent(agent_id: str):
    reg = _get_registry()
    agent = reg.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return agent.to_dict()


@router.get("/network/agents/{agent_id}/job")
def get_job_description(agent_id: str):
    reg = _get_registry()
    agent = reg.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return {
        "agent_id": agent_id,
        "full_name": agent.full_name,
        "job_description": agent.job_description,
        "responsibilities": agent.RESPONSIBILITIES,
        "capabilities": agent.CAPABILITIES,
        "system_prompt": agent.SYSTEM_PROMPT,
    }


@router.post("/network/agents/{agent_id}/think")
async def think(agent_id: str, req: RunRequest):
    reg = _get_registry()
    agent = reg.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    result = await agent.think(req.prompt, context=req.context)
    return {
        "agent_id": agent_id,
        "full_name": agent.full_name,
        "result": result,
        "status": agent.status,
        "total_runs": agent.total_runs,
    }


@router.post("/network/agents/{agent_id}/generate")
async def generate(agent_id: str, req: RunRequest):
    reg = _get_registry()
    agent = reg.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    result = await agent.generate(req.prompt)
    return {
        "agent_id": agent_id,
        "full_name": agent.full_name,
        "result": result,
        "status": agent.status,
        "total_runs": agent.total_runs,
    }


@router.get("/network/departments")
def list_departments():
    reg = _get_registry()
    return reg.departments()


@router.get("/network/stats")
def network_stats():
    reg = _get_registry()
    return reg.stats()


@router.post("/network/broadcast")
async def broadcast(req: MessageRequest):
    reg = _get_registry()
    tasks = []
    for agent_id, agent in reg._agents.items():
        if agent_id != req.dst or req.dst == "*":
            tasks.append(agent.send(req.dst if req.dst != "*" else agent_id, req.msg_type, req.payload))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return {"broadcasted": len(results), "errors": sum(1 for r in results if isinstance(r, Exception))}


@router.post("/network/start")
async def start_network(base_port: int = 9000):
    reg = _get_registry()
    await reg.start_network(base_port=base_port)
    return {"started": True, "agents": len(reg.list_all()), "base_port": base_port}


@router.get("/network/peers/{agent_id}")
def get_peers(agent_id: str):
    reg = _get_registry()
    agent = reg.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return {
        "agent_id": agent_id,
        "peers": agent.peers,
        "peer_count": len(agent.peers),
    }


@router.get("/network/jobs")
def all_job_descriptions():
    reg = _get_registry()
    return reg.job_descriptions()
