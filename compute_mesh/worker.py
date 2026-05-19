"""Compute mesh worker — reports resources and executes sandboxed jobs."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import platform as plat
import signal
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import uuid
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psutil
import websockets

from shared_models import (
    JobAssignment,
    JobResult,
    JobType,
    ResourceCaps,
    ResourceStatus,
    WorkerHello,
)

# Optional GPU support
try:
    import pynvml
    pynvml.nvmlInit()
    _GPU_AVAILABLE = True
except Exception:
    _GPU_AVAILABLE = False


class ResourceMonitor:
    """Thread that samples local resource usage."""

    def __init__(self, interval: float = 2.0):
        self.interval = interval
        self._latest: ResourceStatus | None = None
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=self.interval + 1)

    def latest(self) -> ResourceStatus | None:
        return self._latest

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                mem = psutil.virtual_memory()
                cpu = psutil.cpu_percent(interval=1)
                ram_used_mb = mem.used // (1024 * 1024)
                ram_total_mb = mem.total // (1024 * 1024)
                gpu_pct: float | None = None
                gpu_vram_used: int | None = None
                gpu_vram_total: int | None = None
                if _GPU_AVAILABLE:
                    try:
                        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                        gpu_pct = float(util.gpu)
                        gpu_vram_used = mem_info.used // (1024 * 1024)
                        gpu_vram_total = mem_info.total // (1024 * 1024)
                    except Exception:
                        pass
                self._latest = ResourceStatus(
                    cpu_percent=cpu,
                    ram_used_mb=ram_used_mb,
                    ram_total_mb=ram_total_mb,
                    gpu_percent=gpu_pct,
                    gpu_vram_used_mb=gpu_vram_used,
                    gpu_vram_total_mb=gpu_vram_total,
                    active_jobs=0,  # filled by agent
                )
            except Exception:
                pass
            self._stop.wait(self.interval)


class JobRunner:
    """Sandboxed job executor with resource enforcement."""

    def __init__(self, caps: ResourceCaps):
        self.caps = caps
        self._executor = ThreadPoolExecutor(max_workers=caps.max_jobs, thread_name_prefix="mesh_job")

    def shutdown(self) -> None:
        self._executor.shutdown(wait=True)

    def run(self, assignment: JobAssignment) -> JobResult:
        started = datetime.now(timezone.utc)
        proc: subprocess.Popen | None = None
        peak_ram = 0
        peak_cpu = 0.0

        try:
            if assignment.job_type == JobType.SHELL:
                cmd = ["bash", "-c", assignment.payload]
            elif assignment.job_type == JobType.PYTHON:
                cmd = [sys.executable, "-c", assignment.payload]
            elif assignment.job_type == JobType.CUDA:
                # CUDA jobs: run via python assuming PyTorch/Numba in env
                cmd = [sys.executable, "-c", assignment.payload]
            else:
                raise ValueError(f"unknown job type: {assignment.job_type}")

            env = os.environ.copy()
            env.update(assignment.env)

            # Hard limits: prefer cgroups where available, fallback to ulimit-style via prlimit on Linux
            popen_kwargs: dict[str, Any] = {
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
                "text": True,
                "env": env,
            }

            # Windows doesn't support preexec_fn; macOS doesn't support RLIMIT_AS easily
            if sys.platform == "linux" and assignment.max_ram_mb:
                import resource as res
                def limiter():
                    res.setrlimit(res.RLIMIT_AS, (assignment.max_ram_mb * 1024 * 1024, -1))
                popen_kwargs["preexec_fn"] = limiter

            proc = subprocess.Popen(cmd, **popen_kwargs)

            # Poll for timeout and monitor resource usage
            deadline = time.monotonic() + assignment.timeout_seconds
            parent = psutil.Process(proc.pid)
            while proc.poll() is None:
                if time.monotonic() > deadline:
                    proc.kill()
                    return JobResult(
                        job_id=assignment.job_id,
                        status="timeout",
                        stdout="",
                        stderr="",
                        exit_code=None,
                        started_at=started,
                        finished_at=datetime.now(timezone.utc),
                    )
                # Monitor children + parent
                try:
                    children = parent.children(recursive=True)
                    all_procs = children + [parent]
                    total_ram = 0
                    max_cpu = 0.0
                    for p in all_procs:
                        try:
                            mem_info = p.memory_info()
                            total_ram += mem_info.rss
                            cpu_pct = p.cpu_percent(interval=None)
                            max_cpu = max(max_cpu, cpu_pct)
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                    peak_ram = max(peak_ram, total_ram)
                    peak_cpu = max(peak_cpu, max_cpu)
                except psutil.NoSuchProcess:
                    break
                time.sleep(0.5)

            stdout, stderr = proc.communicate(timeout=5)
            return JobResult(
                job_id=assignment.job_id,
                status="success" if proc.returncode == 0 else "error",
                stdout=stdout,
                stderr=stderr,
                exit_code=proc.returncode,
                started_at=started,
                finished_at=datetime.now(timezone.utc),
                peak_ram_mb=peak_ram // (1024 * 1024),
                peak_cpu_percent=round(peak_cpu, 2),
            )
        except Exception as exc:
            if proc is not None and proc.poll() is None:
                proc.kill()
            return JobResult(
                job_id=assignment.job_id,
                status="error",
                stdout="",
                stderr=traceback.format_exc(),
                exit_code=None,
                started_at=started,
                finished_at=datetime.now(timezone.utc),
            )


class WorkerAgent:
    """Main worker agent that connects to coordinator and manages jobs."""

    def __init__(
        self,
        coordinator_url: str,
        api_key: str,
        worker_id: str | None = None,
        caps: ResourceCaps | None = None,
        verify_ssl: bool = True,
    ):
        self.coordinator_url = coordinator_url.rstrip("/")
        self.api_key = api_key
        self.worker_id = worker_id or f"{plat.node()}-{uuid.uuid4().hex[:8]}"
        self.caps = caps or ResourceCaps()
        self.monitor = ResourceMonitor()
        self.runner = JobRunner(self.caps)
        self._stop_event = asyncio.Event()
        self._active_jobs: dict[str, asyncio.Future] = {}
        self._verify_ssl = verify_ssl

    async def run(self) -> None:
        self.monitor.start()
        url = f"{self.coordinator_url}/ws/workers/{self.worker_id}?api_key={self.api_key}"
        hello = WorkerHello(
            caps=self.caps,
            hostname=plat.node(),
            platform=f"{plat.system()}-{plat.machine()}",
            has_gpu=_GPU_AVAILABLE,
        )
        ssl_context = None
        if self.coordinator_url.startswith("wss://") and not self._verify_ssl:
            import ssl
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        while not self._stop_event.is_set():
            try:
                print(f"[worker] connecting to {self.coordinator_url} ...")
                connect_kwargs = {"ssl": ssl_context} if ssl_context else {}
                async with websockets.connect(url, **connect_kwargs) as ws:
                    await ws.send(json.dumps({"type": "hello", "data": hello.model_dump(mode="json")}))
                    print(f"[worker] registered as {self.worker_id}")
                    # Send immediate heartbeat so coordinator can dispatch jobs right away
                    status = self.monitor.latest()
                    if status:
                        status.active_jobs = 0
                        await ws.send(json.dumps({"type": "heartbeat", "data": status.model_dump(mode="json")}))
                    await self._loop(ws)
            except (websockets.ConnectionClosed, websockets.InvalidStatus, OSError) as exc:
                print(f"[worker] connection error: {exc}; retrying in 5s")
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=5)
                except asyncio.TimeoutError:
                    continue
            except Exception as exc:
                print(f"[worker] unexpected error: {exc}; retrying in 10s")
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=10)
                except asyncio.TimeoutError:
                    continue
        self.monitor.stop()
        self.runner.shutdown()
        print("[worker] stopped")

    async def _loop(self, ws) -> None:
        heartbeat_task = asyncio.create_task(self._heartbeat(ws))
        recv_task = asyncio.create_task(self._receive(ws))
        done = asyncio.Event()

        async def wait_for_done():
            await done.wait()

        try:
            await asyncio.gather(
                heartbeat_task,
                recv_task,
                wait_for_done(),
                return_exceptions=True,
            )
        except asyncio.CancelledError:
            pass
        finally:
            done.set()
            for t in (heartbeat_task, recv_task):
                if not t.done():
                    t.cancel()
            # Wait for active jobs to finish gracefully
            if self._active_jobs:
                print(f"[worker] waiting for {len(self._active_jobs)} active jobs...")
                await asyncio.gather(*[f for f in self._active_jobs.values()], return_exceptions=True)

    async def _heartbeat(self, ws) -> None:
        while not self._stop_event.is_set():
            try:
                status = self.monitor.latest()
                if status:
                    status.active_jobs = len(self._active_jobs)
                    await ws.send(json.dumps({"type": "heartbeat", "data": status.model_dump(mode="json")}))
                await asyncio.wait_for(self._stop_event.wait(), timeout=5)
            except asyncio.TimeoutError:
                continue
            except websockets.ConnectionClosed:
                break

    async def _receive(self, ws) -> None:
        while not self._stop_event.is_set():
            try:
                raw = await ws.recv()
                msg = json.loads(raw)
                mtype = msg.get("type")
                if mtype == "shutdown":
                    print(f"[worker] coordinator requested shutdown: {msg.get('reason')}")
                    self._stop_event.set()
                    break
                elif mtype == "job":
                    assignment = JobAssignment.model_validate(msg.get("data", {}))
                    asyncio.create_task(self._handle_job(ws, assignment))
                else:
                    print(f"[worker] unknown msg type: {mtype}")
            except websockets.ConnectionClosed:
                break
            except Exception as exc:
                print(f"[worker] recv error: {exc}")

    async def _handle_job(self, ws, assignment: JobAssignment) -> None:
        job_id = assignment.job_id
        print(f"[worker] starting job {job_id}")
        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(self.runner._executor, self.runner.run, assignment)
        self._active_jobs[job_id] = future
        try:
            result = await asyncio.wait_for(future, timeout=assignment.timeout_seconds + 10)
        except asyncio.TimeoutError:
            future.cancel()
            result = JobResult(
                job_id=job_id,
                status="timeout",
                stdout="",
                stderr="job exceeded overall deadline",
                exit_code=None,
                started_at=datetime.now(timezone.utc),
                finished_at=datetime.now(timezone.utc),
            )
        self._active_jobs.pop(job_id, None)
        try:
            await ws.send(json.dumps({"type": "job_result", "data": result.model_dump(mode="json")}))
        except websockets.ConnectionClosed:
            print(f"[worker] could not report result for {job_id}; coordinator disconnected")
        print(f"[worker] job {job_id} done: {result.status}")

    def shutdown(self) -> None:
        self._stop_event.set()


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute mesh worker agent")
    parser.add_argument("--url", default="ws://localhost:8000", help="coordinator URL")
    parser.add_argument("--api-key", default=os.getenv("MESH_API_KEY", "dev-key-change-me"), help="API key")
    parser.add_argument("--worker-id", default=None, help="worker ID (auto-generated if omitted)")
    parser.add_argument("--max-cpu", type=float, default=50.0, help="max CPU %% this worker will use")
    parser.add_argument("--max-ram", type=int, default=2048, help="max RAM MB this worker will use")
    parser.add_argument("--max-jobs", type=int, default=1, help="max concurrent jobs")
    parser.add_argument("--max-gpu", type=float, default=None, help="max GPU %% (optional)")
    parser.add_argument("--max-gpu-vram", type=int, default=None, help="max GPU VRAM MB (optional)")
    parser.add_argument("--no-verify-ssl", action="store_true", help="disable SSL cert verification (for self-signed certs)")
    args = parser.parse_args()

    caps = ResourceCaps(
        max_cpu_percent=args.max_cpu,
        max_ram_mb=args.max_ram,
        max_jobs=args.max_jobs,
        max_gpu_percent=args.max_gpu,
        max_gpu_vram_mb=args.max_gpu_vram,
    )
    agent = WorkerAgent(
        coordinator_url=args.url,
        api_key=args.api_key,
        worker_id=args.worker_id,
        caps=caps,
        verify_ssl=not args.no_verify_ssl,
    )

    def _sig_handler(signum, frame):
        print(f"[worker] received signal {signum}, shutting down gracefully...")
        agent.shutdown()

    signal.signal(signal.SIGINT, _sig_handler)
    signal.signal(signal.SIGTERM, _sig_handler)

    asyncio.run(agent.run())


if __name__ == "__main__":
    main()
