#!/usr/bin/env python3
"""
Ollama-like Model Runner for Mac Compute Node
Runs local LLM inference via Ollama HTTP API for embeddings, OCR, summarization.
"""
import asyncio
import json
import os
import time
from typing import Dict, List, Optional

import aiohttp
import requests


class ModelRunner:
    """Manages local AI model execution via Ollama."""

    def __init__(self, config: Dict):
        self.host = config.get("host", "http://localhost:11434")
        self.default_model = config.get("default_model", "llama3.2")
        self.embedding_model = config.get("embedding_model", "nomic-embed-text")
        self.available_models: List[str] = config.get("models", ["llama3.2"])
        self._model_status: Dict[str, bool] = {}
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def _check_ollama(self) -> bool:
        try:
            r = requests.get(f"{self.host}/api/tags", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def _pull_if_needed(self, model: str):
        """Pull a model if not present."""
        try:
            r = requests.post(
                f"{self.host}/api/pull",
                json={"name": model, "stream": False},
                timeout=300,
            )
            return r.status_code == 200
        except Exception:
            return False

    async def run_task(self, task: Dict) -> Dict:
        """Dispatch task to appropriate model endpoint."""
        task_type = task.get("type", "generic")
        content = task.get("content", "")

        handlers = {
            "embed": self._embed,
            "summarize": self._summarize,
            "ocr": self._ocr,
            "code_review": self._code_review,
            "vision": self._vision,
            "data_process": self._data_process,
            "generic": self._generic,
        }

        handler = handlers.get(task_type, self._generic)
        return await handler(content, task)

    async def _embed(self, content: str, task: Dict) -> Dict:
        """Generate embeddings via Ollama."""
        if not self._check_ollama():
            return {"error": "Ollama not available", "embedding": []}

        session = await self._get_session()
        payload = {
            "model": self.embedding_model,
            "prompt": content[:4000],  # Truncate for speed
        }
        async with session.post(f"{self.host}/api/embeddings", json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                return {
                    "embedding": data.get("embedding", []),
                    "model": self.embedding_model,
                    "dimensions": len(data.get("embedding", [])),
                }
            return {"error": f"Embed failed: {resp.status}"}

    async def _summarize(self, content: str, task: Dict) -> Dict:
        """Summarize text via local LLM."""
        if not self._check_ollama():
            return {"error": "Ollama not available", "summary": ""}

        prompt = (
            f"Summarize the following text in 3-5 sentences:\n\n{content[:8000]}\n\nSummary:"
        )
        return await self._generate(prompt, self.default_model)

    async def _ocr(self, content: str, task: Dict) -> Dict:
        """Extract text from image (placeholder; uses llava if available)."""
        if not self._check_ollama():
            return {"error": "Ollama not available", "text": ""}

        # If image path provided, use vision model
        image_path = task.get("image_path")
        if image_path and os.path.exists(image_path):
            vision_model = task.get("vision_model", "llava")
            # llava-based OCR
            prompt = "Extract all text from this image. Return only the extracted text."
            # Ollama vision API uses base64 images
            import base64
            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            payload = {
                "model": vision_model,
                "prompt": prompt,
                "images": [b64],
                "stream": False,
            }
            session = await self._get_session()
            async with session.post(f"{self.host}/api/generate", json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"text": data.get("response", ""), "model": vision_model}
        return {"text": content, "note": "Fallback text extraction"}

    async def _code_review(self, content: str, task: Dict) -> Dict:
        """Review code for issues and improvements."""
        if not self._check_ollama():
            return {"error": "Ollama not available", "review": ""}

        prompt = (
            f"Review this code for bugs, security issues, and improvements. "
            f"Be concise.\n\n```\n{content[:6000]}\n```\n\nReview:"
        )
        return await self._generate(prompt, self.default_model)

    async def _vision(self, content: str, task: Dict) -> Dict:
        """Vision task (image description/classification)."""
        image_path = task.get("image_path")
        if not image_path or not os.path.exists(image_path):
            return {"error": "No image provided"}
        return await self._ocr(content, task)  # Reuse OCR/vision path

    async def _data_process(self, content: str, task: Dict) -> Dict:
        """Process structured data (JSON/CSV)."""
        try:
            # Attempt to parse and analyze
            data = json.loads(content) if content.strip().startswith("{") else content
            return {
                "parsed": True,
                "type": type(data).__name__,
                "length": len(data) if hasattr(data, "__len__") else 0,
                "preview": str(data)[:500],
            }
        except json.JSONDecodeError:
            return {"parsed": False, "raw": content[:1000]}

    async def _generic(self, content: str, task: Dict) -> Dict:
        """Generic generation task."""
        prompt = task.get("prompt", f"Process this: {content[:4000]}")
        return await self._generate(prompt, self.default_model)

    async def _generate(self, prompt: str, model: str) -> Dict:
        """Call Ollama generate endpoint."""
        session = await self._get_session()
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 512,
            },
        }
        start = time.time()
        async with session.post(f"{self.host}/api/generate", json=payload) as resp:
            latency = time.time() - start
            if resp.status == 200:
                data = await resp.json()
                return {
                    "response": data.get("response", ""),
                    "model": model,
                    "latency_ms": round(latency * 1000, 2),
                    "tokens_evaluated": data.get("eval_count", 0),
                }
            return {"error": f"Generate failed: {resp.status}"}

    def get_status(self) -> Dict:
        """Return model runner status."""
        ollama_up = self._check_ollama()
        return {
            "ollama_available": ollama_up,
            "host": self.host,
            "default_model": self.default_model,
            "embedding_model": self.embedding_model,
            "models": self.available_models,
        }

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
