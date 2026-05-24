"""Local Inference — Run lightweight LLM inference on the host machine.

Provides an HTTP inference server and a convenience wrapper so that
the LLM OS can call local models when cloud APIs are unavailable or
when latency matters.
"""

import json
import os
import subprocess
import threading
import time
from dataclasses import dataclass, field
from typing import Optional

from llm_os.inference import InferenceResult


@dataclass
class InferenceStats:
    """Performance stats for local inference."""
    tokens_per_second: float = 0.0
    avg_latency_ms: float = 0.0
    total_requests: int = 0
    total_tokens: int = 0
    model_loaded: bool = False


class LocalInferenceRunner:
    """Run inference against a locally-hosted model (e.g. via Ollama, llama.cpp)."""

    def __init__(self, model_name: str = "llama3", host: str = "http://localhost:11434"):
        self.model_name = model_name
        self.host = host.rstrip("/")
        self.stats = InferenceStats()

    def is_available(self) -> bool:
        try:
            import urllib.request
            req = urllib.request.Request(f"{self.host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode())
                models = [m.get("name", "") for m in data.get("models", [])]
                return self.model_name in models or any(
                    self.model_name in m for m in models
                )
        except Exception:
            return False

    def generate(self, prompt: str, system_prompt: str = "",
                 max_tokens: int = 1024) -> InferenceResult:
        if not self.is_available():
            return InferenceResult(
                text="", model=self.model_name, provider="local",
                success=False, error="Local model not available",
            )
        import urllib.request

        payload = {
            "model": self.model_name,
            "prompt": f"{system_prompt}\n\n{prompt}" if system_prompt else prompt,
            "stream": False,
            "options": {"num_predict": max_tokens},
        }
        t0 = time.time()
        try:
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                f"{self.host}/api/generate", data=data,
                headers={"Content-Type": "application/json"}, method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode())
        except Exception as exc:
            return InferenceResult(
                text="", model=self.model_name, provider="local",
                success=False, error=str(exc),
                latency_ms=(time.time() - t0) * 1000,
            )

        latency = (time.time() - t0) * 1000
        text = body.get("response", "")
        tokens = body.get("eval_count", len(text.split()))
        self.stats.total_requests += 1
        self.stats.total_tokens += tokens
        if latency > 0:
            self.stats.tokens_per_second = tokens / (latency / 1000)
        self.stats.avg_latency_ms = (
            (self.stats.avg_latency_ms * (self.stats.total_requests - 1) + latency)
            / self.stats.total_requests
        )
        return InferenceResult(
            text=text, model=self.model_name, provider="local",
            tokens_used=tokens, cost_usd=0.0, latency_ms=latency,
        )


class InferenceServer:
    """Thin HTTP wrapper that serves local model inference.

    Useful for exposing a model to the economic engine or external
    clients who pay per-request.
    """

    def __init__(self, runner: Optional[LocalInferenceRunner] = None,
                 port: int = 8421):
        self.runner = runner or LocalInferenceRunner()
        self.port = port
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        from http.server import HTTPServer, BaseHTTPRequestHandler

        runner = self.runner

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length)) if length else {}
                result = runner.generate(
                    body.get("prompt", ""),
                    system_prompt=body.get("system_prompt", ""),
                    max_tokens=body.get("max_tokens", 1024),
                )
                resp = json.dumps({
                    "text": result.text,
                    "model": result.model,
                    "tokens": result.tokens_used,
                    "latency_ms": result.latency_ms,
                    "success": result.success,
                }).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(resp)

            def log_message(self, fmt, *args):
                pass  # silence logs

        server = HTTPServer(("0.0.0.0", self.port), Handler)
        self._thread = threading.Thread(target=server.serve_forever, daemon=True)
        self._thread.start()

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()


def quick_inference(prompt: str, model: str = "llama3") -> str:
    """One-liner: send a prompt to the local model and return the text."""
    runner = LocalInferenceRunner(model_name=model)
    result = runner.generate(prompt)
    return result.text if result.success else f"[error] {result.error}"


def estimate_inference_speed(model: str = "llama3", sample_tokens: int = 50) -> dict:
    """Benchmark local inference speed."""
    runner = LocalInferenceRunner(model_name=model)
    if not runner.is_available():
        return {"available": False, "model": model}
    t0 = time.time()
    result = runner.generate("Count from 1 to 50.", max_tokens=sample_tokens)
    elapsed = time.time() - t0
    return {
        "available": True,
        "model": model,
        "tokens": result.tokens_used,
        "elapsed_s": round(elapsed, 3),
        "tokens_per_second": round(result.tokens_used / max(elapsed, 0.001), 1),
    }
