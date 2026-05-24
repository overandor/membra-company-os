"""Membra Decentralized Model Registry — every node keeps a replica."""
from __future__ import annotations

import hashlib
import json
import os
import platform as plat
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, Request

from network_discovery import DiscoveryProtocol
from shared_models import ModelCard, ModelShard, NodeCapabilities, NodeState, RegistryGossip

API_KEY = os.getenv("MEMBRA_API_KEY", "dev-key-change-me")
NODE_ID = os.getenv("MEMBRA_NODE_ID", f"node-{plat.node()}-{uuid.uuid4().hex[:6]}")
API_PORT = int(os.getenv("MEMBRA_API_PORT", "8765"))


def _auth(request: Request) -> bool:
    auth = request.headers.get("authorization", "")
    expected = f"Bearer {API_KEY}"
    return auth == expected


@asynccontextmanager
async def lifespan(app: FastAPI):
    discovery: DiscoveryProtocol = app.state.discovery
    await discovery.start()
    yield
    await discovery.stop()


app = FastAPI(title="membra-model-hub registry", lifespan=lifespan)
app.state.discovery = DiscoveryProtocol(
    node_id=NODE_ID,
    api_port=API_PORT,
    bootstrap_peers=os.getenv("MEMBRA_BOOTSTRAP_PEERS", "").split(",") if os.getenv("MEMBRA_BOOTSTRAP_PEERS") else [],
)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path in ("/health", "/docs", "/openapi.json", "/redoc", "/gossip", "/models", "/nodes"):
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
        "status": "ok",
        "peers": len(d.peers),
        "models_known": len(d.models),
        "api_endpoint": d.api_endpoint,
    }


@app.get("/models")
async def list_models(tag: str | None = None) -> list[ModelCard]:
    d = app.state.discovery
    models = list(d.models.values())
    if tag:
        models = [m for m in models if tag in m.tags]
    return models


@app.get("/models/{model_id}")
async def get_model(model_id: str) -> ModelCard:
    d = app.state.discovery
    if model_id not in d.models:
        raise HTTPException(status_code=404, detail="model not found")
    return d.models[model_id]


@app.post("/models")
async def publish_model(card: ModelCard, request: Request) -> dict[str, str]:
    if not _auth(request):
        raise HTTPException(status_code=401, detail="unauthorized")
    d = app.state.discovery
    # Ensure model_id uniqueness
    card.created_at = datetime.now(timezone.utc)
    d.models[card.model_id] = card
    await d.announce_model(card)
    return {"status": "published", "model_id": card.model_id}


@app.post("/gossip")
async def receive_gossip(gossip: RegistryGossip) -> dict[str, Any]:
    d = app.state.discovery
    await d._merge_gossip(gossip.model_dump(mode="json"))
    # Return our own state so caller can merge back
    return RegistryGossip(
        node=NodeState(
            node_id=NODE_ID,
            hostname=plat.node(),
            api_endpoint=d.api_endpoint,
            ws_endpoint=d.ws_endpoint,
            caps=NodeCapabilities(),
        ),
        models=list(d.models.values()),
        known_peers=list(d.peers.keys()),
    ).model_dump(mode="json")


@app.get("/nodes")
async def list_nodes() -> list[NodeState]:
    return list(app.state.discovery.peers.values())


@app.get("/nodes/{node_id}")
async def get_node(node_id: str) -> NodeState:
    d = app.state.discovery
    if node_id not in d.peers:
        raise HTTPException(status_code=404, detail="node not found")
    return d.peers[node_id]


@app.post("/nodes/{node_id}/announce")
async def announce_node(state: NodeState, request: Request) -> dict[str, str]:
    if not _auth(request):
        raise HTTPException(status_code=401, detail="unauthorized")
    d = app.state.discovery
    d.peers[state.node_id] = state
    return {"status": "ack"}
