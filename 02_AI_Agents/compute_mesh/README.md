# compute_mesh

Consensual distributed compute mesh. Workers opt-in, set their own resource caps, and execute sandboxed jobs dispatched by a central coordinator.

## Quick start

### 1. Install

```bash
cd compute_mesh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Generate TLS certs (optional, recommended for internet)

```bash
python generate_certs.py --hostname your-domain.com
export MESH_TLS_CERT=certs/cert.pem
export MESH_TLS_KEY=certs/key.pem
```

Workers use `--no-verify-ssl` for self-signed certs.

### 3. Start coordinator

```bash
export MESH_API_KEY="change-me-to-a-long-secret"
# Optional: Redis or Postgres persistence
export MESH_REDIS_URL="redis://localhost:6379/0"
# export MESH_POSTGRES_DSN="postgres://user:pass@localhost:5432/meshdb"
python coordinator.py
```

### 4. Connect a worker

```bash
export MESH_API_KEY="change-me-to-a-long-secret"
python worker.py --url ws://localhost:8000 \
  --max-cpu 50 \
  --max-ram 2048 \
  --max-jobs 1
```

The worker owner controls every cap. The coordinator cannot override them.

### 5. Submit a job

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Authorization: Bearer change-me-to-a-long-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "shell",
    "payload": "echo hello from $(hostname)",
    "timeout_seconds": 30,
    "max_cpu_percent": 20,
    "max_ram_mb": 512
  }'
```

Then poll for results:

```bash
curl http://localhost:8000/jobs/<job_id> \
  -H "Authorization: Bearer change-me-to-a-long-secret"
```

## Architecture

- **Coordinator** (`coordinator.py`): FastAPI server with WebSocket worker registry and REST job dispatch. Picks workers greedily based on advertised capacity. Supports pluggable persistence (memory, Redis, Postgres) and TLS.
- **Worker** (`worker.py`): Python agent that heartbeats resource status, accepts jobs over WebSocket, and spawns sandboxed subprocesses. Supports Linux hard limits via `RLIMIT_AS`, cross-platform soft monitoring via `psutil`, and WSS.
- **Backends** (`backends.py`): Pluggable persistence layer — `MemoryBackend`, `RedisBackend`, `PostgresBackend`.
- **Rate Limiter** (`rate_limiter.py`): Sliding-window rate limiter with Redis or in-memory backends.
- **Shared models** (`shared_models.py`): Pydantic schemas for jobs, resources, and messages.

## Security / consent design

1. **Worker-side caps** — the worker binary enforces `max_cpu`, `max_ram`, `max_jobs`, etc. The coordinator only sees advertised limits and must respect them.
2. **API key auth** — both workers and job submitters must present `Bearer <MESH_API_KEY>`.
3. **Subprocess sandboxing** — jobs run as child processes; `preexec_fn` sets Linux `RLIMIT_AS` when available.
4. **Graceful shutdown** — `SIGTERM`/`SIGINT` lets active jobs finish before exit.
5. **No inbound holes** — workers open an outbound WebSocket. No listener required on worker side.
6. **Rate limiting** — sliding-window rate limits on job submission (`MESH_RATE_WINDOW_SECONDS`, `MESH_RATE_MAX_JOBS_PER_WINDOW`).
7. **TLS** — optional HTTPS/WSS with self-signed or real certs.

## Docker / compose

```bash
cd compute_mesh
docker compose up -d --build --scale worker=3
```

This starts: Redis, Postgres, coordinator, and 3 workers with Docker resource limits.

## GPU support

Install `pynvml` (via `nvidia-ml-py`) and pass `--max-gpu` / `--max-gpu-vram`. The worker will report GPU utilization and VRAM usage in heartbeats.

## Production checklist

- [x] Replace in-memory registries with Redis / Postgres.
- [x] Add TLS (`wss://`, `https://`) and mTLS for worker auth.
- [x] Add rate limits and per-client job quotas.
- [ ] Add job queues (Redis, RabbitMQ, or SQS) instead of synchronous dispatch.
- [x] Run workers inside containers with cgroup limits.
- [ ] Add audit logging for every job and result.
- [ ] Add mTLS for worker authentication beyond API keys.
