#!/usr/bin/env python3
"""
Ollama Hub — Self-hosted LLM inference on Apple Silicon.
Runs on your Mac. Uses your own compute. No API keys.
"""

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, List, Optional

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

# Recommended models for different tasks on Apple Silicon
MODEL_REGISTRY = {
    "general": {"model": "llama3.2:1b", "size_gb": 1.3, "purpose": "General Q&A, lightweight tasks"},
    "coding": {"model": "deepseek-coder:1.3b", "size_gb": 0.8, "purpose": "Code completion, review"},
    "reasoning": {"model": "deepseek-r1:latest", "size_gb": 5.2, "purpose": "Deep analysis, reasoning"},
    "chat": {"model": "qwen2.5:0.5b", "size_gb": 0.4, "purpose": "Fast chat, summarization"},
    "embeddings": {"model": "nomic-embed-text", "size_gb": 0.3, "purpose": "Text embeddings, RAG"},
    "vision": {"model": "llava:latest", "size_gb": 4.5, "purpose": "Image understanding"},
    "code_quality": {"model": "phi3:mini", "size_gb": 2.2, "purpose": "Code quality, review"},
    "docs": {"model": "llama3.1:8b", "size_gb": 4.9, "purpose": "Documentation, writing"},
}


@dataclass
class ModelInfo:
    name: str
    size: str
    parameter_size: str
    format: str
    family: str
    families: List[str]
    modified_at: str


class OllamaHub:
    """Central hub for local LLM inference via Ollama."""

    def __init__(self, host: str = OLLAMA_HOST):
        self.host = host.rstrip("/")
        self._ensure_ollama()

    def _ensure_ollama(self) -> bool:
        """Check if Ollama is installed and running."""
        try:
            result = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                print("ERROR: Ollama not found. Install: curl -fsSL https://ollama.com/install.sh | sh")
                return False
        except FileNotFoundError:
            print("ERROR: Ollama not found. Install: curl -fsSL https://ollama.com/install.sh | sh")
            return False

        # Check if server is running
        import urllib.request
        try:
            req = urllib.request.Request(f"{self.host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            print("Ollama not running. Starting server...")
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3)
            try:
                req = urllib.request.Request(f"{self.host}/api/tags", method="GET")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    return resp.status == 200
            except Exception:
                print("ERROR: Could not start Ollama server")
                return False

    def list_models(self) -> List[ModelInfo]:
        import urllib.request
        req = urllib.request.Request(f"{self.host}/api/tags")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return [
                ModelInfo(
                    name=m["name"],
                    size=m.get("size", ""),
                    parameter_size=m.get("details", {}).get("parameter_size", ""),
                    format=m.get("details", {}).get("format", ""),
                    family=m.get("details", {}).get("family", ""),
                    families=m.get("details", {}).get("families", []),
                    modified_at=m.get("modified_at", ""),
                )
                for m in data.get("models", [])
            ]

    def pull_model(self, model_name: str) -> Iterator[str]:
        """Pull a model from Ollama registry. Yields progress lines."""
        import urllib.request
        payload = json.dumps({"name": model_name}).encode()
        req = urllib.request.Request(
            f"{self.host}/api/pull",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            for line in resp:
                try:
                    msg = json.loads(line)
                    status = msg.get("status", "")
                    if "completed" in status.lower() or "downloading" in status.lower():
                        yield status
                    elif "error" in msg:
                        yield f"ERROR: {msg['error']}"
                except json.JSONDecodeError:
                    continue

    def ensure_models(self, models: List[str]) -> Dict[str, bool]:
        """Ensure specified models are available. Pull if missing."""
        available = {m.name for m in self.list_models()}
        results = {}
        for model in models:
            if model in available:
                results[model] = True
                print(f"  {model}: already available")
                continue
            print(f"  Pulling {model}...")
            for line in self.pull_model(model):
                print(f"    {line}")
            # Verify
            available = {m.name for m in self.list_models()}
            results[model] = model in available
        return results

    def generate(self, model: str, prompt: str, system: str = "", stream: bool = False, temperature: float = 0.7, num_predict: int = 400) -> str:
        import urllib.request
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": stream,
            "options": {"temperature": temperature, "num_predict": num_predict},
        }
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{self.host}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            if stream:
                full = ""
                for line in resp:
                    try:
                        msg = json.loads(line)
                        if "response" in msg:
                            full += msg["response"]
                        if msg.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
                return full
            else:
                result = json.loads(resp.read())
                return result.get("response", "")

    def chat(self, model: str, messages: List[Dict[str, str]], stream: bool = False) -> str:
        import urllib.request
        payload = {"model": model, "messages": messages, "stream": stream}
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{self.host}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read())
            return result.get("message", {}).get("content", "")

    def embed(self, model: str, text: str) -> List[float]:
        import urllib.request
        payload = {"model": model, "input": text}
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{self.host}/api/embed",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            return result.get("embeddings", [[]])[0]

    def generate_for_project(self, project_root: str, task: str, context: str = "") -> Dict:
        """Generate LLM output specific to a project context."""
        project_name = Path(project_root).name
        model = MODEL_REGISTRY["general"]["model"]

        system = f"You are an expert software engineer assisting with the project '{project_name}'."
        prompt = f"Task: {task}\n\nContext:\n{context}\n\nProvide a concise, actionable response."

        response = self.generate(model, prompt, system=system, temperature=0.3, num_predict=600)
        return {
            "project": project_name,
            "task": task,
            "model": model,
            "response": response,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }


def main():
    hub = OllamaHub()
    print("=== Ollama Hub ===")
    print(f"Host: {OLLAMA_HOST}")

    models = hub.list_models()
    print(f"Available models: {len(models)}")
    for m in models:
        print(f"  {m.name} ({m.parameter_size})")

    # Pull recommended models
    print("\nEnsuring recommended models...")
    to_pull = [v["model"] for v in MODEL_REGISTRY.values()]
    results = hub.ensure_models(list(set(to_pull)))
    print(f"Ready: {sum(results.values())}/{len(results)}")


if __name__ == "__main__":
    main()
