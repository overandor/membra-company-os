"""Shared Pydantic models for membra-model-hub."""
from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


class ModelFormat(str, enum.Enum):
    OLLAMA = "ollama"
    GGUF = "gguf"
    SAFETENSORS = "safetensors"
    PYTORCH = "pytorch"
    ONNX = "onnx"


class ModelShard(BaseModel):
    """A shard (file chunk) of a model."""

    shard_id: str
    file_hash: str  # sha256
    size_bytes: int
    node_ids: list[str] = Field(default_factory=list)


class ModelCard(BaseModel):
    """Public metadata for a model, like a Hugging Face model card."""

    model_id: str  # org/name format
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    format: ModelFormat = ModelFormat.OLLAMA
    parameters: str = ""  # e.g. "7B"
    quantization: str = ""  # e.g. "Q4_K_M"
    license: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    shards: list[ModelShard] = Field(default_factory=list)
    total_size_bytes: int = 0
    inference_endpoint_path: str = "/v1/chat/completions"


class NodeCapabilities(BaseModel):
    """What a worker node can do."""

    max_cpu_percent: float = Field(default=50.0, ge=0, le=100)
    max_ram_mb: int = Field(default=4096, ge=0)
    max_gpu_vram_mb: int | None = Field(default=None, ge=0)
    max_concurrent_jobs: int = Field(default=1, ge=1)
    models_hosted: list[str] = Field(default_factory=list)


class NodeState(BaseModel):
    """Live state of a peer node."""

    node_id: str
    hostname: str
    api_endpoint: str  # http://host:port
    ws_endpoint: str | None = None
    caps: NodeCapabilities
    health: Literal["healthy", "degraded", "unhealthy"] = "healthy"
    active_jobs: int = 0
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InferenceRequest(BaseModel):
    """User submits an inference request."""

    model_id: str
    prompt: str
    max_tokens: int = Field(default=256, ge=1, le=8192)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    stream: bool = False
    system_prompt: str | None = None


class InferenceResult(BaseModel):
    """Result of an inference job."""

    task_id: str
    model_id: str
    status: Literal["success", "error", "timeout", "cancelled"]
    output: str = ""
    tokens_generated: int = 0
    duration_ms: int = 0
    node_id: str = ""
    proof_hash: str = ""  # sha256 of output for verification


class RegistryGossip(BaseModel):
    """Message exchanged during gossip rounds."""

    node: NodeState
    models: list[ModelCard] = Field(default_factory=list)
    known_peers: list[str] = Field(default_factory=list)
