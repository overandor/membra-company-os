#!/usr/bin/env python3
"""
Mac Compute Node — Core Engine
Orchestrates containers, AI models, file mining, and L2 settlement.
"""
import asyncio
import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import psutil
import yaml

from .container_manager import ContainerManager
from .file_miner import FileMiner
from .model_runner import ModelRunner

# Real chain integration
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from chain_bridge import ComputeToChainBridge


@dataclass
class NodeResources:
    cpu_cores: int = 0
    cpu_percent: float = 0.0
    memory_total_gb: float = 0.0
    memory_used_gb: float = 0.0
    memory_percent: float = 0.0
    disk_total_gb: float = 0.0
    disk_used_gb: float = 0.0
    disk_percent: float = 0.0
    gpu_available: bool = False
    timestamp: float = 0.0


class ComputeEngine:
    """Central orchestrator for the Mac Compute Node."""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "..", "config.yaml"
        )
        with open(self.config_path) as f:
            self.config = yaml.safe_load(f)

        self.node_id = self._generate_node_id()
        self.started_at = time.time()
        self.running = False

        # Subsystems
        self.containers = ContainerManager(self.config["containers"])
        self.models = ModelRunner(self.config["ollama"])
        self.miner = FileMiner(self.config["mining"])

        # Metrics
        self.total_tasks = 0
        self.total_earnings = 0.0
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.current_jobs: List[Dict] = []
        self.resources = NodeResources()

        # Real chain bridge (lazy init to avoid circular import issues)
        self.chain_bridge: Optional[ComputeToChainBridge] = None

        # State file
        self.state_file = os.path.expanduser("~/.mac_compute_node/state.json")
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        self._load_state()

    def _generate_node_id(self) -> str:
        """Generate a unique node ID based on machine fingerprint."""
        import hashlib
        machine = f"{os.uname().nodename}-{psutil.cpu_count()}-{psutil.virtual_memory().total}"
        return hashlib.sha256(machine.encode()).hexdigest()[:16]

    def _load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file) as f:
                state = json.load(f)
                self.total_tasks = state.get("total_tasks", 0)
                self.total_earnings = state.get("total_earnings", 0.0)
                self.tasks_completed = state.get("tasks_completed", 0)
                self.tasks_failed = state.get("tasks_failed", 0)

    def _save_state(self):
        with open(self.state_file, "w") as f:
            json.dump(
                {
                    "node_id": self.node_id,
                    "total_tasks": self.total_tasks,
                    "total_earnings": self.total_earnings,
                    "tasks_completed": self.tasks_completed,
                    "tasks_failed": self.tasks_failed,
                    "updated_at": time.time(),
                },
                f,
                indent=2,
            )

    def get_resources(self) -> NodeResources:
        """Snapshot current resource utilization."""
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        self.resources = NodeResources(
            cpu_cores=psutil.cpu_count(logical=True),
            cpu_percent=psutil.cpu_percent(interval=0.5),
            memory_total_gb=round(mem.total / (1024**3), 2),
            memory_used_gb=round(mem.used / (1024**3), 2),
            memory_percent=mem.percent,
            disk_total_gb=round(disk.total / (1024**3), 2),
            disk_used_gb=round(disk.used / (1024**3), 2),
            disk_percent=round(disk.percent, 2),
            gpu_available=self._check_gpu(),
            timestamp=time.time(),
        )
        return self.resources

    def _check_gpu(self) -> bool:
        """Check for Apple Silicon GPU or CUDA."""
        try:
            if sys := __import__("sys"):
                if sys.platform == "darwin":
                    import subprocess
                    result = subprocess.run(
                        ["system_profiler", "SPDisplaysDataType", "-json"],
                        capture_output=True,
                        text=True,
                    )
                    return "Apple" in result.stdout
        except Exception:
            pass
        return False

    async def start(self):
        """Start the compute node engine."""
        self.running = True
        self.get_resources()
        print(f"[ENGINE] Node {self.node_id} started")
        print(f"[ENGINE] Resources: {self.resources.cpu_cores} cores, "
              f"{self.resources.memory_total_gb}GB RAM")

        # Start background loops
        await asyncio.gather(
            self._resource_monitor_loop(),
            self._task_processor_loop(),
        )

    async def stop(self):
        """Graceful shutdown."""
        self.running = False
        self._save_state()
        print("[ENGINE] Stopped")

    async def _resource_monitor_loop(self, interval: int = 5):
        while self.running:
            self.get_resources()
            await asyncio.sleep(interval)

    async def _task_processor_loop(self):
        """Main loop: scan files, spawn containers, run models, settle to L2."""
        while self.running:
            try:
                # Only process if under resource limits
                if self._can_accept_work():
                    tasks = self.miner.scan_for_tasks()
                    for task in tasks:
                        await self._execute_task(task)
                await asyncio.sleep(2)
            except Exception as e:
                print(f"[ENGINE] Task loop error: {e}")
                await asyncio.sleep(5)

    def _can_accept_work(self) -> bool:
        """Check if node is under configured resource limits."""
        cfg = self.config["node"]
        return (
            self.resources.cpu_percent < cfg["max_cpu_percent"]
            and self.resources.memory_percent < cfg["max_memory_percent"]
            and self.resources.disk_percent < cfg["max_disk_percent"]
        )

    async def _execute_task(self, task: Dict):
        """Execute a compute task: container + model inference."""
        self.total_tasks += 1
        job = {
            "id": f"job-{self.total_tasks}",
            "task": task,
            "started": time.time(),
            "status": "running",
        }
        self.current_jobs.append(job)

        try:
            # 1. Run model inference on file content
            result = await self.models.run_task(task)

            # 2. Optionally containerize for isolation
            if task.get("containerize"):
                result = await self.containers.run_workload(task, result)

            # 3. Record earnings
            reward = self.config["mining"]["task_rewards"].get(task["type"], 0.001)
            self.total_earnings += reward
            self.tasks_completed += 1

            # 4. Submit on-chain reward via real chain bridge
            if self.chain_bridge is not None:
                try:
                    value_score = min(100, max(1, len(str(result)) / 100))
                    self.chain_bridge.queue_reward(
                        task_id=job["id"],
                        task_type=task["type"],
                        value_score=value_score,
                        worker_node=self.node_id,
                    )
                except Exception as ce:
                    print(f"[CHAIN] Reward enqueue failed: {ce}")

            job["status"] = "completed"
            job["result"] = result
            job["earnings"] = reward

        except Exception as e:
            self.tasks_failed += 1
            job["status"] = "failed"
            job["error"] = str(e)

        finally:
            job["finished"] = time.time()
            self.current_jobs = [j for j in self.current_jobs if j["id"] != job["id"]]
            self._save_state()

    def get_status(self) -> Dict:
        return {
            "node_id": self.node_id,
            "running": self.running,
            "uptime": round(time.time() - self.started_at, 2),
            "resources": self.resources.__dict__,
            "tasks": {
                "total": self.total_tasks,
                "completed": self.tasks_completed,
                "failed": self.tasks_failed,
                "active": len(self.current_jobs),
            },
            "earnings": {
                "total": round(self.total_earnings, 6),
                "currency": self.config["marketplace"]["token_symbol"],
            },
            "jobs": self.current_jobs,
        }
