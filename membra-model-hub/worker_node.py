"""Membra Model Worker — hosts models and serves inference requests."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import platform as plat
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn

from network_discovery import DiscoveryProtocol
from shared_models import InferenceRequest, InferenceResult, ModelCard, NodeCapabilities, NodeState

API_KEY = os.getenv("MEMBRA_API_KEY", "dev-key-change-me")
NODE_ID = os.getenv("MEMBRA_NODE_ID", f"worker-{plat.node()}-{uuid.uuid4().hex[:6]}")
API_PORT = int(os.getenv("MEMBRA_WORKER_PORT", "8766"))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

app = FastAPI(title="membra-model-hub worker")


class WorkerState:
    def __init__(self):
        self.active_jobs: dict[str, asyncio.Task] = {}
        self.models_hosted: list[str] = []
        self._lock = asyncio.Lock()

    async def start_job(self, task_id: str, task: asyncio.Task) -> None:
        async with self._lock:
            self.active_jobs[task_id] = task

    async def finish_job(self, task_id: str) -> None:
        async with self._lock:
            self.active_jobs.pop(task_id, None)

    @property
    def active_count(self) -> int:
        return len(self.active_jobs)


worker_state = WorkerState()


def _auth(request: Request) -> bool:
    auth = request.headers.get("authorization", "")
    expected = f"Bearer {API_KEY}"
    return auth == expected


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path in ("/health", "/docs", "/openapi.json", "/redoc", "/gossip"):
        return await call_next(request)
    if request.method == "OPTIONS":
        return await call_next(request)
    if not _auth(request):
        return JSONResponse(status_code=401, content={"detail": "invalid or missing api key"})
    return await call_next(request)


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "node_id": NODE_ID,
        "role": "worker",
        "models_hosted": worker_state.models_hosted,
        "active_jobs": worker_state.active_count,
        "api_endpoint": app.state.discovery.api_endpoint if hasattr(app.state, "discovery") else None,
    }


@app.get("/v1/models")
async def list_local_models() -> list[str]:
    """Return models this worker currently hosts."""
    return worker_state.models_hosted


@app.post("/v1/inference")
async def run_inference(req: InferenceRequest) -> dict[str, Any]:
    if req.model_id not in worker_state.models_hosted:
        raise HTTPException(status_code=404, detail="model not hosted on this node")

    task_id = f"wk-{uuid.uuid4().hex[:12]}"
    started = time.monotonic()

    async def _do() -> dict[str, Any]:
        try:
            # Use Ollama as the local inference backend
            messages = []
            if req.system_prompt:
                messages.append({"role": "system", "content": req.system_prompt})
            messages.append({"role": "user", "content": req.prompt})

            ollama_req = {
                "model": req.model_id,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": req.temperature,
                    "top_p": req.top_p,
                    "num_predict": req.max_tokens,
                },
            }
            async with httpx.AsyncClient(timeout=120.0) as client:
                r = await client.post(f"{OLLAMA_URL}/api/chat", json=ollama_req)
            if r.status_code != 200:
                return {
                    "output": f"Ollama error: {r.status_code} {r.text}",
                    "tokens_generated": 0,
                    "duration_ms": int((time.monotonic() - started) * 1000),
                    "proof_hash": "",
                }
            data = r.json()
            output = data.get("message", {}).get("content", "")
            eval_count = data.get("eval_count", 0)
            proof = hashlib.sha256(output.encode()).hexdigest()
            return {
                "output": output,
                "tokens_generated": eval_count,
                "duration_ms": int((time.monotonic() - started) * 1000),
                "proof_hash": proof,
            }
        except Exception as exc:
            return {
                "output": str(exc),
                "tokens_generated": 0,
                "duration_ms": int((time.monotonic() - started) * 1000),
                "proof_hash": "",
            }

    task = asyncio.create_task(_do())
    await worker_state.start_job(task_id, task)
    try:
        result = await asyncio.wait_for(task, timeout=req.max_tokens * 2 + 30)
    except asyncio.TimeoutError:
        task.cancel()
        result = {
            "output": "inference timeout",
            "tokens_generated": 0,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "proof_hash": "",
        }
    await worker_state.finish_job(task_id)
    return result


@app.post("/gossip")
async def receive_gossip(request: Request) -> Any:
    body = await request.json()
    d = app.state.discovery
    await d._merge_gossip(body)
    return {
        "node_id": NODE_ID,
        "role": "worker",
        "models_hosted": worker_state.models_hosted,
        "active_jobs": worker_state.active_count,
    }


async def announce_to_registry(discovery: DiscoveryProtocol, model_id: str) -> None:
    """Tell the network we host this model."""
    card = ModelCard(
        model_id=model_id,
        format="ollama",
        tags=["llm", "local"],
    )
    await discovery.announce_model(card)
    # Also push to known peers directly
    for peer in discovery.peers.values():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{peer.api_endpoint}/models",
                    json=card.model_dump(mode="json"),
                    headers={"authorization": f"Bearer {API_KEY}"},
                )
        except Exception:
            pass


class WorkerAgent:
    def __init__(self, models: list[str], bootstrap_peers: list[str] | None = None):
        self.models = models
        self.bootstrap_peers = bootstrap_peers or []
        self.discovery = DiscoveryProtocol(
            node_id=NODE_ID,
            api_port=API_PORT,
            bootstrap_peers=self.bootstrap_peers,
        )
        self._stop = asyncio.Event()

    async def run(self) -> None:
        await self.discovery.start()
        # Announce hosted models
        for m in self.models:
            worker_state.models_hosted.append(m)
            await announce_to_registry(self.discovery, m)
        print(f"[worker {NODE_ID}] serving models: {self.models}")
        print(f"[worker {NODE_ID}] endpoint: {self.discovery.api_endpoint}")
        # Keep-alive loop
        while not self._stop.is_set():
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=10)
            except asyncio.TimeoutError:
                # Re-announce models periodically so registry stays fresh
                for m in self.models:
                    await announce_to_registry(self.discovery, m)
        await self.discovery.stop()

    def shutdown(self) -> None:
        self._stop.set()


def main() -> None:
    parser = argparse.ArgumentParser(description="Membra Model Worker")
    parser.add_argument("--models", required=True, help="Comma-separated Ollama model names (e.g. llama3.1:8b,phi3)")
    parser.add_argument("--port", type=int, default=API_PORT, help="HTTP API port")
    parser.add_argument("--bootstrap", default="", help="Comma-separated bootstrap peer URLs")
    args = parser.parse_args()

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    peers = [p.strip() for p in args.bootstrap.split(",") if p.strip()]

    agent = WorkerAgent(models=models, bootstrap_peers=peers)

    def _sig(signum, frame):
        print(f"\n[worker] signal {signum}, shutting down...")
        agent.shutdown()

    signal.signal(signal.SIGINT, _sig)
    signal.signal(signal.SIGTERM, _sig)

    # Start discovery in background
    asyncio.create_task(agent.run())

    # Start FastAPI
    app.state.discovery = agent.discovery
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="info")


if __name__ == "__main__":
    main()
