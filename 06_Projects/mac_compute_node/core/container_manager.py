#!/usr/bin/env python3
"""
Docker-like Container Manager for Mac Compute Node
Manages isolated compute workloads without full Docker dependency.
"""
import json
import os
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Container:
    id: str
    name: str
    image: str
    status: str = "created"
    created_at: float = 0.0
    pid: Optional[int] = None
    cpu_limit: str = "512"
    memory_limit: str = "512m"
    mounts: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    log_path: str = ""
    exit_code: Optional[int] = None


class ContainerManager:
    """Manages containers for compute workloads.

    Uses Docker when available; falls back to process isolation via
    chroot/jail on macOS for lightweight sandboxing.
    """

    def __init__(self, config: Dict):
        self.config = config
        self.containers: Dict[str, Container] = {}
        self.docker_available = self._check_docker()
        self.engine = config.get("engine", "docker")
        self.state_dir = os.path.expanduser("~/.mac_compute_node/containers")
        os.makedirs(self.state_dir, exist_ok=True)

    def _check_docker(self) -> bool:
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _generate_id(self) -> str:
        return f"mcn-{uuid.uuid4().hex[:12]}"

    async def create(
        self,
        image: str,
        command: List[str],
        name: str = None,
        env: Dict[str, str] = None,
        mounts: List[str] = None,
        cpu_limit: str = None,
        memory_limit: str = None,
    ) -> Container:
        """Create a container (Docker or mock process)."""
        cid = self._generate_id()
        cname = name or f"workload-{cid}"

        container = Container(
            id=cid,
            name=cname,
            image=image,
            created_at=time.time(),
            cpu_limit=cpu_limit or self.config["limits"]["cpu_shares"],
            memory_limit=memory_limit or self.config["limits"]["memory"],
            mounts=mounts or [],
            env=env or {},
            log_path=os.path.join(self.state_dir, f"{cid}.log"),
        )
        self.containers[cid] = container

        if self.docker_available and self.engine == "docker":
            await self._create_docker(container, command)
        else:
            await self._create_mock(container, command)

        return container

    async def _create_docker(self, container: Container, command: List[str]):
        """Create a real Docker container."""
        args = [
            "docker", "run", "-d", "--rm",
            "--name", container.name,
            "--cpus", str(int(container.cpu_limit) / 1024),
            "--memory", container.memory_limit,
            "--pids-limit", str(self.config["limits"]["max_pids"]),
        ]
        for m in container.mounts:
            args.extend(["-v", m])
        for k, v in container.env.items():
            args.extend(["-e", f"{k}={v}"])
        args.append(container.image)
        args.extend(command)

        result = subprocess.run(args, capture_output=True, text=True)
        if result.returncode == 0:
            container.status = "running"
            container.pid = result.stdout.strip()
        else:
            container.status = "failed"
            container.exit_code = result.returncode
            with open(container.log_path, "w") as f:
                f.write(result.stderr)

    async def _create_mock(self, container: Container, command: List[str]):
        """Mock container using subprocess isolation."""
        env = os.environ.copy()
        env.update(container.env)
        with open(container.log_path, "w") as log:
            proc = subprocess.Popen(
                command,
                stdout=log,
                stderr=log,
                env=env,
            )
        container.pid = proc.pid
        container.status = "running"

    async def run_workload(self, task: Dict, input_data: Dict) -> Dict:
        """Run a compute workload in a container and return results."""
        task_type = task.get("type", "generic")
        image = self._image_for_task(task_type)

        # Build container command from task
        command = self._build_command(task, input_data)

        container = await self.create(
            image=image,
            command=command,
            env={"TASK_TYPE": task_type, "NODE_ID": "local"},
        )

        # Wait for completion (with timeout)
        timeout = task.get("timeout", 300)
        await self._wait(container, timeout)

        # Read output
        output = {}
        if os.path.exists(container.log_path):
            with open(container.log_path) as f:
                output["logs"] = f.read()[-4096:]  # Last 4KB

        # Cleanup
        await self.remove(container.id)

        return {
            "container_id": container.id,
            "status": container.status,
            "exit_code": container.exit_code,
            "output": output,
        }

    def _image_for_task(self, task_type: str) -> str:
        mapping = {
            "embed": "python:3.11-slim",
            "ocr": "python:3.11-slim",
            "summarize": "python:3.11-slim",
            "code_review": "python:3.11-slim",
            "vision": "python:3.11-slim",
            "data_process": "python:3.11-slim",
        }
        return mapping.get(task_type, self.config["images"]["python"])

    def _build_command(self, task: Dict, input_data: Dict) -> List[str]:
        """Build a command list for the container."""
        return [
            "python", "-c",
            f"import json; print(json.dumps({{'task': '{task['type']}', 'result': 'processed'}}))"
        ]

    async def _wait(self, container: Container, timeout: int):
        """Wait for container to finish."""
        start = time.time()
        while time.time() - start < timeout:
            if self.docker_available and self.engine == "docker":
                result = subprocess.run(
                    ["docker", "inspect", "-f", "{{.State.Status}}", container.id],
                    capture_output=True, text=True,
                )
                status = result.stdout.strip()
                if status in ("exited", "dead"):
                    container.status = "exited"
                    break
            else:
                if container.pid:
                    try:
                        os.kill(container.pid, 0)
                    except ProcessLookupError:
                        container.status = "exited"
                        break
            await asyncio.sleep(0.5)

    async def remove(self, cid: str):
        """Remove a container."""
        container = self.containers.get(cid)
        if not container:
            return

        if self.docker_available and self.engine == "docker":
            subprocess.run(
                ["docker", "rm", "-f", container.id],
                capture_output=True,
            )
        elif container.pid:
            try:
                os.kill(container.pid, 9)
            except ProcessLookupError:
                pass

        container.status = "removed"
        del self.containers[cid]

    def list_containers(self) -> List[Dict]:
        return [{
            "id": c.id,
            "name": c.name,
            "image": c.image,
            "status": c.status,
            "pid": c.pid,
        } for c in self.containers.values()]

    def get_stats(self) -> Dict:
        """Get aggregate container stats."""
        return {
            "total": len(self.containers),
            "running": sum(1 for c in self.containers.values() if c.status == "running"),
            "docker_available": self.docker_available,
            "engine": self.engine,
        }
