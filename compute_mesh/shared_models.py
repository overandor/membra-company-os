"""Shared Pydantic models for compute_mesh."""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ResourceCaps(BaseModel):
    """Resource caps set by the worker owner."""

    max_cpu_percent: float = Field(default=50.0, ge=0, le=100)
    max_ram_mb: int = Field(default=2048, ge=0)
    max_gpu_percent: float | None = Field(default=None, ge=0, le=100)
    max_gpu_vram_mb: int | None = Field(default=None, ge=0)
    max_jobs: int = Field(default=1, ge=1)


class ResourceStatus(BaseModel):
    """Live resource report from worker."""

    cpu_percent: float
    ram_used_mb: int
    ram_total_mb: int
    gpu_percent: float | None = None
    gpu_vram_used_mb: int | None = None
    gpu_vram_total_mb: int | None = None
    active_jobs: int


class JobType(str, enum.Enum):
    SHELL = "shell"
    PYTHON = "python"
    CUDA = "cuda"


class JobRequest(BaseModel):
    """Client submits a job to the coordinator."""

    job_type: JobType
    payload: str = ""
    env: dict[str, str] = Field(default_factory=dict)
    timeout_seconds: int = Field(default=60, ge=1)
    max_cpu_percent: float | None = Field(default=None, ge=0, le=100)
    max_ram_mb: int | None = Field(default=None, ge=0)
    needs_gpu: bool = False
    gpu_vram_mb: int | None = Field(default=None, ge=0)


class JobAssignment(BaseModel):
    """Coordinator pushes a job to a worker."""

    job_id: str
    job_type: JobType
    payload: str
    env: dict[str, str]
    timeout_seconds: int
    max_cpu_percent: float | None = None
    max_ram_mb: int | None = None


class JobResult(BaseModel):
    """Worker reports result back to coordinator."""

    job_id: str
    status: Literal["success", "error", "timeout", "cancelled"]
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    started_at: datetime
    finished_at: datetime
    peak_ram_mb: int | None = None
    peak_cpu_percent: float | None = None


class WorkerHello(BaseModel):
    """Initial worker registration message."""

    caps: ResourceCaps
    hostname: str
    platform: str
    has_gpu: bool = False


class WorkerMessage(BaseModel):
    """Union type for messages worker -> coordinator."""

    type: Literal["hello", "heartbeat", "job_result", "log"]
    data: WorkerHello | ResourceStatus | JobResult | dict[str, Any]
