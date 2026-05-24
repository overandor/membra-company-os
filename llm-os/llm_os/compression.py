"""Compression — Model weight compression utilities for deployment.

Supports quantisation and pruning so trained models can be packaged
into the DMG desktop app or served on constrained hardware.
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class CompressionResult:
    """Result of a model compression run."""
    original_size_mb: float
    compressed_size_mb: float
    compression_ratio: float
    method: str
    quality_loss_estimate: float
    output_path: Optional[str] = None
    duration_seconds: float = 0.0
    metadata: dict = field(default_factory=dict)


class ModelCompressor:
    """Compress model checkpoints for lightweight deployment."""

    METHODS = ("quantize_int8", "quantize_int4", "prune_magnitude", "distill_stub")

    def __init__(self, storage_dir: str = "/tmp/llm_os_compressed"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self.history: list = []

    def compress(self, checkpoint_path: str, method: str = "quantize_int8") -> CompressionResult:
        """Compress a model checkpoint.

        For now this performs a simulated compression (measures size,
        estimates output) because real quantisation requires PyTorch/ONNX
        which may not be installed.  The interface is stable so that
        callers can swap in real compression later.
        """
        if method not in self.METHODS:
            raise ValueError(f"Unknown method {method!r}; choose from {self.METHODS}")

        t0 = time.time()
        original_size = self._get_size_mb(checkpoint_path)

        ratio_map = {
            "quantize_int8": 0.50,
            "quantize_int4": 0.25,
            "prune_magnitude": 0.60,
            "distill_stub": 0.10,
        }
        quality_loss_map = {
            "quantize_int8": 0.02,
            "quantize_int4": 0.08,
            "prune_magnitude": 0.05,
            "distill_stub": 0.15,
        }

        ratio = ratio_map[method]
        compressed_size = original_size * ratio

        out_name = (
            f"compressed_{method}_{hashlib.sha256(checkpoint_path.encode()).hexdigest()[:8]}.bin"
        )
        out_path = os.path.join(self.storage_dir, out_name)

        # Write a placeholder so downstream code can stat the file
        with open(out_path, "wb") as fh:
            fh.write(b"\x00" * max(1, int(compressed_size * 1024)))

        result = CompressionResult(
            original_size_mb=original_size,
            compressed_size_mb=compressed_size,
            compression_ratio=ratio,
            method=method,
            quality_loss_estimate=quality_loss_map[method],
            output_path=out_path,
            duration_seconds=time.time() - t0,
        )
        self.history.append(result)
        return result

    @staticmethod
    def _get_size_mb(path: str) -> float:
        if os.path.isfile(path):
            return os.path.getsize(path) / (1024 * 1024)
        if os.path.isdir(path):
            total = sum(
                os.path.getsize(os.path.join(dp, f))
                for dp, _, fnames in os.walk(path)
                for f in fnames
            )
            return total / (1024 * 1024)
        return 0.0


def compress_model_for_dmg(checkpoint_path: str, method: str = "quantize_int4") -> CompressionResult:
    """One-shot helper used by the DMG app builder."""
    return ModelCompressor().compress(checkpoint_path, method)
