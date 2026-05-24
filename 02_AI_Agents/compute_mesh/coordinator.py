"""Compute mesh coordinator — accepts workers and dispatches jobs."""
from __future__ import annotations

import asyncio
import json
import os
import secrets
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.security import HTTPBearer
from pydantic import ValidationError

from backends import MeshBackend, create_backend
from rate_limiter import RateLimiter, create_rate_limiter
from shared_models import (
    JobAssignment,
    JobRequest,
    JobResult,
    ResourceStatus,
    WorkerHello,
    WorkerMessage,
)

API_KEY = os.getenv("MESH_API_KEY", "dev-key-change-me")
AUTH_SCHEME = HTTPBearer(auto_error=False)


class WorkerState:
    """Runtime state for a connected worker."""

    def __init__(self, ws: WebSocket, hello: WorkerHello):
        self.ws = ws
        self.hello = hello
        self.status: ResourceStatus | None = None
        self.active_jobs: set[str] = set()
        self.connected_at = datetime.now(timezone.utc)

    @property
    def available(self) -> bool:
        return len(self.active_jobs) < self.hello.caps.max_jobs

    def fits(self, req: JobRequest) -> bool:
        caps = self.hello.caps
        if req.needs_gpu and not self.hello.has_gpu:
            return False
        if req.max_cpu_percent and caps.max_cpu_percent < req.max_cpu_percent:
            return False
        if req.max_ram_mb and caps.max_ram_mb < req.max_ram_mb:
            return False
        if req.gpu_vram_mb and (caps.max_gpu_vram_mb is None or caps.max_gpu_vram_mb < req.gpu_vram_mb):
            return False
        return True


class MeshRuntime:
    """Runtime in-memory state backed by persistent backend."""

    def __init__(self, backend: MeshBackend, rate_limiter: RateLimiter):
        self.backend = backend
        self.rate_limiter = rate_limiter
        self.workers: dict[str, WorkerState] = {}
        self._lock = asyncio.Lock()

    async def register(self, worker_id: str, ws: WebSocket, hello: WorkerHello) -> WorkerState:
        async with self._lock:
            ws.state.worker_id = worker_id  # type: ignore[attr-defined]
            state = WorkerState(ws, hello)
            self.workers[worker_id] = state
            await self.backend.store_worker(worker_id, hello, datetime.now(timezone.utc).isoformat())
            return state

    async def disconnect(self, worker_id: str) -> None:
        async with self._lock:
            self.workers.pop(worker_id, None)
            await self.backend.remove_worker(worker_id)

    async def update_status(self, worker_id: str, status: ResourceStatus) -> None:
        async with self._lock:
            if w := self.workers.get(worker_id):
                w.status = status
            await self.backend.update_worker_status(worker_id, status)

    async def assign_job(self, worker_id: str, assignment: JobAssignment) -> None:
        async with self._lock:
            if w := self.workers.get(worker_id):
                w.active_jobs.add(assignment.job_id)

    async def finish_job(self, worker_id: str, job_id: str) -> None:
        async with self._lock:
            if w := self.workers.get(worker_id):
                w.active_jobs.discard(job_id)

    async def pick_worker(self, req: JobRequest) -> str | None:
        async with self._lock:
            candidates = [
                (wid, w)
                for wid, w in self.workers.items()
                if w.available and w.fits(req)
            ]
            if not candidates:
                return None
            def score(_wid: str, w: WorkerState) -> float:
                s = w.status
                if s is None:
                    return -1.0
                cpu_score = 1.0 - (s.cpu_percent / max(w.hello.caps.max_cpu_percent, 1.0))
                ram_score = 1.0 - (s.ram_used_mb / max(w.hello.caps.max_ram_mb, 1.0))
                return cpu_score + ram_score
            candidates.sort(key=lambda x: score(x[0], x[1]), reverse=True)
            return candidates[0][0]


_backend = create_backend()
_ratelimiter = create_rate_limiter()
state = MeshRuntime(_backend, _ratelimiter)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Graceful shutdown: notify workers
    for wid, ws in list(state.workers.items()):
        try:
            await ws.ws.send_json({"type": "shutdown", "reason": "coordinator stopping"})
        except Exception:
            pass


app = FastAPI(title="compute_mesh coordinator", lifespan=lifespan)


def _auth_ws(websocket: WebSocket) -> bool:
    key = websocket.query_params.get("api_key", "")
    if key != API_KEY:
        return False
    return True


def _auth_headers(headers: dict[str, str]) -> bool:
    auth = headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:] == API_KEY
    return False


@app.websocket("/ws/workers/{worker_id}")
async def worker_ws(websocket: WebSocket, worker_id: str):
    await websocket.accept()
    if not _auth_ws(websocket):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        raw = await websocket.receive_text()
        msg = json.loads(raw)
        if msg.get("type") != "hello":
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        hello = WorkerHello.model_validate(msg.get("data", {}))
    except (json.JSONDecodeError, ValidationError) as exc:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(exc))
        return

    wstate = await state.register(worker_id, websocket, hello)
    print(f"[coordinator] worker {worker_id} registered from {hello.hostname}")

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            mtype = msg.get("type")
            if mtype == "heartbeat":
                wstate.status = ResourceStatus.model_validate(msg.get("data", {}))
            elif mtype == "job_result":
                result = JobResult.model_validate(msg.get("data", {}))
                await state.finish_job(worker_id, result.job_id)
                await state.backend.update_job_result(
                    result.job_id, result.model_dump(mode="json")
                )
                print(f"[coordinator] job {result.job_id} finished with status={result.status}")
            elif mtype == "log":
                print(f"[worker {worker_id}] {msg.get('data', '')}")
    except WebSocketDisconnect:
        pass
    finally:
        await state.disconnect(worker_id)
        print(f"[coordinator] worker {worker_id} disconnected")


RATE_WINDOW = int(os.getenv("MESH_RATE_WINDOW_SECONDS", "60"))
RATE_MAX = int(os.getenv("MESH_RATE_MAX_JOBS_PER_WINDOW", "100"))


@app.post("/jobs")
async def create_job(req: JobRequest) -> dict[str, Any]:
    # Rate limit by a synthetic client key derived from Authorization header (already validated by middleware)
    client_key = "client_default"
    if not await state.rate_limiter.is_allowed(client_key, RATE_WINDOW, RATE_MAX):
        raise HTTPException(status_code=429, detail="rate limit exceeded")

    job_id = str(uuid.uuid4())
    worker_id = await state.pick_worker(req)
    if worker_id is None:
        raise HTTPException(status_code=503, detail="no available workers match requirements")

    assignment = JobAssignment(
        job_id=job_id,
        job_type=req.job_type,
        payload=req.payload,
        env=req.env,
        timeout_seconds=req.timeout_seconds,
        max_cpu_percent=req.max_cpu_percent,
        max_ram_mb=req.max_ram_mb,
    )
    wstate = state.workers[worker_id]
    await state.assign_job(worker_id, assignment)
    job_data = {
        "job_id": job_id,
        "worker_id": worker_id,
        "status": "running",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "request": req.model_dump(mode="json"),
    }
    await state.backend.store_job(job_id, job_data)
    await wstate.ws.send_json({"type": "job", "data": assignment.model_dump(mode="json")})
    return {"job_id": job_id, "worker_id": worker_id, "status": "running"}


@app.get("/jobs/{job_id}")
async def get_job(job_id: str) -> dict[str, Any]:
    job = await state.backend.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.get("/workers")
async def list_workers() -> list[dict[str, Any]]:
    out = []
    persisted = await state.backend.list_workers()
    for wdata in persisted:
        hello = wdata.get("hello", {})
        caps = hello.get("caps", {})
        wid = hello.get("hostname", "unknown")
        out.append({
            "worker_id": wid,
            "hostname": hello.get("hostname", "unknown"),
            "platform": hello.get("platform", "unknown"),
            "has_gpu": hello.get("has_gpu", False),
            "caps": caps,
            "status": wdata.get("status"),
            "active_jobs": 0,
            "connected_at": wdata.get("connected_at", ""),
        })
    # Augment with live runtime data
    for wid, w in state.workers.items():
        for item in out:
            if item["worker_id"] == wid:
                item["status"] = w.status.model_dump(mode="json") if w.status else item.get("status")
                item["active_jobs"] = len(w.active_jobs)
                break
    return out


# Simple header-based auth middleware for REST endpoints
@app.middleware("http")
async def auth_middleware(request, call_next):
    if request.url.path in ("/docs", "/openapi.json", "/redoc"):
        return await call_next(request)
    if request.method == "OPTIONS":
        return await call_next(request)
    auth = request.headers.get("authorization", "")
    expected = f"Bearer {API_KEY}"
    if auth != expected:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=401, content={"detail": "invalid or missing api key"})
    return await call_next(request)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("MESH_PORT", "8000"))
    host = os.getenv("MESH_HOST", "0.0.0.0")
    ssl_keyfile = os.getenv("MESH_TLS_KEY")
    ssl_certfile = os.getenv("MESH_TLS_CERT")
    kwargs: dict[str, Any] = {}
    if ssl_keyfile and ssl_certfile:
        kwargs["ssl_keyfile"] = ssl_keyfile
        kwargs["ssl_certfile"] = ssl_certfile
    uvicorn.run("coordinator:app", host=host, port=port, reload=False, **kwargs)
