"""Pluggable persistence backends for coordinator state."""
from __future__ import annotations

import abc
import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any

from shared_models import JobResult, ResourceStatus, WorkerHello


class MeshBackend(abc.ABC):
    """Abstract backend for workers, jobs, and audit logs."""

    @abc.abstractmethod
    async def store_worker(self, worker_id: str, hello: WorkerHello, connected_at: str) -> None: ...

    @abc.abstractmethod
    async def remove_worker(self, worker_id: str) -> None: ...

    @abc.abstractmethod
    async def update_worker_status(self, worker_id: str, status: ResourceStatus) -> None: ...

    @abc.abstractmethod
    async def list_workers(self) -> list[dict[str, Any]]: ...

    @abc.abstractmethod
    async def store_job(self, job_id: str, data: dict[str, Any]) -> None: ...

    @abc.abstractmethod
    async def get_job(self, job_id: str) -> dict[str, Any] | None: ...

    @abc.abstractmethod
    async def update_job_result(self, job_id: str, result: dict[str, Any]) -> None: ...


class MemoryBackend(MeshBackend):
    """In-memory backend (default, non-persistent)."""

    def __init__(self):
        self.workers: dict[str, dict[str, Any]] = {}
        self.jobs: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def store_worker(self, worker_id: str, hello: WorkerHello, connected_at: str) -> None:
        async with self._lock:
            self.workers[worker_id] = {
                "hello": hello.model_dump(mode="json"),
                "connected_at": connected_at,
                "status": None,
            }

    async def remove_worker(self, worker_id: str) -> None:
        async with self._lock:
            self.workers.pop(worker_id, None)

    async def update_worker_status(self, worker_id: str, status: ResourceStatus) -> None:
        async with self._lock:
            if w := self.workers.get(worker_id):
                w["status"] = status.model_dump(mode="json")

    async def list_workers(self) -> list[dict[str, Any]]:
        async with self._lock:
            return list(self.workers.values())

    async def store_job(self, job_id: str, data: dict[str, Any]) -> None:
        async with self._lock:
            self.jobs[job_id] = data

    async def get_job(self, job_id: str) -> dict[str, Any] | None:
        async with self._lock:
            return self.jobs.get(job_id)

    async def update_job_result(self, job_id: str, result: dict[str, Any]) -> None:
        async with self._lock:
            if j := self.jobs.get(job_id):
                j["result"] = result
                j["status"] = result.get("status", "unknown")


class RedisBackend(MeshBackend):
    """Redis-backed persistence."""

    def __init__(self, redis_url: str):
        import redis.asyncio as redis
        self._redis = redis.from_url(redis_url, decode_responses=True)
        self._prefix = "mesh"

    async def store_worker(self, worker_id: str, hello: WorkerHello, connected_at: str) -> None:
        key = f"{self._prefix}:worker:{worker_id}"
        await self._redis.hset(key, mapping={
            "hello": json.dumps(hello.model_dump(mode="json")),
            "connected_at": connected_at,
            "status": json.dumps(None),
        })

    async def remove_worker(self, worker_id: str) -> None:
        await self._redis.delete(f"{self._prefix}:worker:{worker_id}")

    async def update_worker_status(self, worker_id: str, status: ResourceStatus) -> None:
        key = f"{self._prefix}:worker:{worker_id}"
        await self._redis.hset(key, "status", json.dumps(status.model_dump(mode="json")))

    async def list_workers(self) -> list[dict[str, Any]]:
        out = []
        async for key in self._redis.scan_iter(match=f"{self._prefix}:worker:*"):
            data = await self._redis.hgetall(key)
            out.append({
                "hello": json.loads(data.get("hello", "{}")),
                "connected_at": data.get("connected_at", ""),
                "status": json.loads(data.get("status", "null")),
            })
        return out

    async def store_job(self, job_id: str, data: dict[str, Any]) -> None:
        key = f"{self._prefix}:job:{job_id}"
        await self._redis.set(key, json.dumps(data))

    async def get_job(self, job_id: str) -> dict[str, Any] | None:
        key = f"{self._prefix}:job:{job_id}"
        raw = await self._redis.get(key)
        return json.loads(raw) if raw else None

    async def update_job_result(self, job_id: str, result: dict[str, Any]) -> None:
        key = f"{self._prefix}:job:{job_id}"
        raw = await self._redis.get(key)
        if raw:
            data = json.loads(raw)
            data["result"] = result
            data["status"] = result.get("status", "unknown")
            await self._redis.set(key, json.dumps(data))


class PostgresBackend(MeshBackend):
    """Postgres-backed persistence."""

    def __init__(self, dsn: str):
        self._dsn = dsn
        self._pool = None

    async def _ensure_pool(self):
        if self._pool is None:
            import asyncpg
            self._pool = await asyncpg.create_pool(self._dsn, min_size=1, max_size=10)
            async with self._pool.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS mesh_workers (
                        worker_id TEXT PRIMARY KEY,
                        hello JSONB NOT NULL,
                        connected_at TIMESTAMPTZ NOT NULL,
                        status JSONB
                    )
                """)
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS mesh_jobs (
                        job_id UUID PRIMARY KEY,
                        data JSONB NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)

    async def store_worker(self, worker_id: str, hello: WorkerHello, connected_at: str) -> None:
        await self._ensure_pool()
        import asyncpg
        async with self._pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO mesh_workers (worker_id, hello, connected_at, status)
                   VALUES ($1, $2, $3, $4)
                   ON CONFLICT (worker_id) DO UPDATE
                   SET hello = EXCLUDED.hello, connected_at = EXCLUDED.connected_at, status = EXCLUDED.status""",
                worker_id, json.dumps(hello.model_dump(mode="json")), connected_at, None,
            )

    async def remove_worker(self, worker_id: str) -> None:
        await self._ensure_pool()
        async with self._pool.acquire() as conn:
            await conn.execute("DELETE FROM mesh_workers WHERE worker_id = $1", worker_id)

    async def update_worker_status(self, worker_id: str, status: ResourceStatus) -> None:
        await self._ensure_pool()
        async with self._pool.acquire() as conn:
            await conn.execute(
                "UPDATE mesh_workers SET status = $1 WHERE worker_id = $2",
                json.dumps(status.model_dump(mode="json")), worker_id,
            )

    async def list_workers(self) -> list[dict[str, Any]]:
        await self._ensure_pool()
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("SELECT hello, connected_at, status FROM mesh_workers")
        return [{"hello": r["hello"], "connected_at": r["connected_at"].isoformat(), "status": r["status"]} for r in rows]

    async def store_job(self, job_id: str, data: dict[str, Any]) -> None:
        await self._ensure_pool()
        async with self._pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO mesh_jobs (job_id, data)
                   VALUES ($1, $2)
                   ON CONFLICT (job_id) DO UPDATE SET data = EXCLUDED.data""",
                job_id, json.dumps(data),
            )

    async def get_job(self, job_id: str) -> dict[str, Any] | None:
        await self._ensure_pool()
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT data FROM mesh_jobs WHERE job_id = $1", job_id)
        return json.loads(row["data"]) if row else None

    async def update_job_result(self, job_id: str, result: dict[str, Any]) -> None:
        await self._ensure_pool()
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT data FROM mesh_jobs WHERE job_id = $1", job_id)
            if row:
                data = json.loads(row["data"])
                data["result"] = result
                data["status"] = result.get("status", "unknown")
                await conn.execute(
                    "UPDATE mesh_jobs SET data = $1 WHERE job_id = $2",
                    json.dumps(data), job_id,
                )


def create_backend() -> MeshBackend:
    """Factory: reads env vars and returns the right backend."""
    redis_url = os.getenv("MESH_REDIS_URL")
    pg_dsn = os.getenv("MESH_POSTGRES_DSN")
    if redis_url:
        return RedisBackend(redis_url)
    if pg_dsn:
        return PostgresBackend(pg_dsn)
    return MemoryBackend()
