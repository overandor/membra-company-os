"""Inference router — accepts user prompts and dispatches to model-hosting nodes."""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import platform as plat
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, status

from network_discovery import DiscoveryProtocol
from shared_models import InferenceRequest, InferenceResult, NodeCapabilities, NodeState

API_KEY = os.getenv("MEMBRA_API_KEY", "dev-key-change-me")
NODE_ID = os.getenv("MEMBRA_NODE_ID", f"router-{plat.node()}-{uuid.uuid4().hex[:6]}")
API_PORT = int(os.getenv("MEMBRA_API_PORT", "8765"))
INFERENCE_TIMEOUT = int(os.getenv("MEMBRA_INFERENCE_TIMEOUT", "120"))


def _auth(request: Request) -> bool:
    auth = request.headers.get("authorization", "")
    expected = f"Bearer {API_KEY}"
    return auth == expected


class RouterState:
    def __init__(self):
        self.tasks: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def start_task(self, req: InferenceRequest, node_id: str) -> str:
        task_id = f"inf-{uuid.uuid4().hex[:16]}"
        async with self._lock:
            self.tasks[task_id] = {
                "task_id": task_id,
                "model_id": req.model_id,
                "status": "running",
                "node_id": node_id,
                "submitted_at": datetime.now(timezone.utc).isoformat(),
                "result": None,
            }
        return task_id

    async def finish_task(self, task_id: str, result: InferenceResult) -> None:
        async with self._lock:
            if task_id in self.tasks:
                self.tasks[task_id]["status"] = result.status
                self.tasks[task_id]["result"] = result.model_dump(mode="json")
                self.tasks[task_id]["finished_at"] = datetime.now(timezone.utc).isoformat()


router_state = RouterState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    discovery: DiscoveryProtocol = app.state.discovery
    await discovery.start()
    yield
    await discovery.stop()


app = FastAPI(title="membra-model-hub inference router", lifespan=lifespan)
app.state.discovery = DiscoveryProtocol(
    node_id=NODE_ID,
    api_port=API_PORT,
    bootstrap_peers=os.getenv("MEMBRA_BOOTSTRAP_PEERS", "").split(",") if os.getenv("MEMBRA_BOOTSTRAP_PEERS") else [],
)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    public = {"/health", "/docs", "/openapi.json", "/redoc", "/gossip", "/models", "/nodes", "/inference", "/inference/"}
    if request.url.path.rstrip("/") in public:
        return await call_next(request)
    if request.method == "OPTIONS":
        return await call_next(request)
    if not _auth(request):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=401, content={"detail": "invalid or missing api key"})
    return await call_next(request)


@app.get("/health")
async def health() -> dict[str, Any]:
    d = app.state.discovery
    return {
        "node_id": NODE_ID,
        "role": "inference_router",
        "peers": len(d.peers),
        "models_known": len(d.models),
        "active_tasks": len(router_state.tasks),
    }


@app.get("/models")
async def list_models(tag: str | None = None) -> list[Any]:
    d = app.state.discovery
    models = list(d.models.values())
    if tag:
        models = [m for m in models if tag in m.tags]
    return [m.model_dump(mode="json") for m in models]


@app.get("/models/{model_id}")
async def get_model(model_id: str) -> Any:
    d = app.state.discovery
    if model_id not in d.models:
        raise HTTPException(status_code=404, detail="model not found")
    return d.models[model_id].model_dump(mode="json")


@app.get("/nodes")
async def list_nodes() -> list[Any]:
    return [n.model_dump(mode="json") for n in app.state.discovery.peers.values()]


@app.post("/gossip")
async def receive_gossip(request: Request) -> Any:
    body = await request.json()
    d = app.state.discovery
    await d._merge_gossip(body)
    return {
        "node_id": NODE_ID,
        "role": "inference_router",
        "models": [m.model_dump(mode="json") for m in d.models.values()],
        "known_peers": list(d.peers.keys()),
    }


def _pick_node_for_model(d: DiscoveryProtocol, model_id: str) -> NodeState | None:
    """Pick the least-loaded healthy node that advertises the model."""
    candidates = []
    for peer in d.peers.values():
        if peer.health != "healthy":
            continue
        if model_id not in peer.caps.models_hosted:
            continue
        candidates.append(peer)
    if not candidates:
        return None
    # Greedy: least active jobs
    candidates.sort(key=lambda p: p.active_jobs)
    return candidates[0]


@app.post("/inference")
async def create_inference(req: InferenceRequest) -> dict[str, str]:
    d = app.state.discovery
    if req.model_id not in d.models:
        raise HTTPException(status_code=404, detail="model not known in network")

    node = _pick_node_for_model(d, req.model_id)
    if node is None:
        raise HTTPException(status_code=503, detail="no healthy nodes hosting this model")

    task_id = await router_state.start_task(req, node.node_id)
    asyncio.create_task(_dispatch_inference(task_id, req, node))
    return {"task_id": task_id, "status": "running", "node_id": node.node_id}


@app.get("/inference/{task_id}")
async def get_inference(task_id: str) -> dict[str, Any]:
    task = router_state.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return task


async def _dispatch_inference(task_id: str, req: InferenceRequest, node: NodeState) -> None:
    try:
        payload = req.model_dump(mode="json")
        async with httpx.AsyncClient(timeout=INFERENCE_TIMEOUT) as client:
            r = await client.post(
                f"{node.api_endpoint}/v1/inference",
                json=payload,
                headers={"authorization": f"Bearer {API_KEY}"},
            )
        if r.status_code == 200:
            data = r.json()
            result = InferenceResult(
                task_id=task_id,
                model_id=req.model_id,
                status="success",
                output=data.get("output", ""),
                tokens_generated=data.get("tokens_generated", 0),
                duration_ms=data.get("duration_ms", 0),
                node_id=node.node_id,
                proof_hash=data.get("proof_hash", ""),
            )
        else:
            result = InferenceResult(
                task_id=task_id,
                model_id=req.model_id,
                status="error",
                output="",
                node_id=node.node_id,
            )
    except Exception as exc:
        result = InferenceResult(
            task_id=task_id,
            model_id=req.model_id,
            status="error",
            output=str(exc),
            node_id=node.node_id,
        )
    await router_state.finish_task(task_id, result)
