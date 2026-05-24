"""MEMBRA CompanyOS — Ollama connector for local LLM inference.
Each employee gets their own connector instance pointing at a local
`ollama serve` instance.
"""
import os
import httpx
from typing import Optional, Dict, Any, List
from app.core.logging import get_logger

logger = get_logger(__name__)

DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_TIMEOUT = 120.0


class OllamaConnector:
    """Lightweight connector to a local Ollama server."""

    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = DEFAULT_OLLAMA_URL,
        timeout: float = DEFAULT_TIMEOUT,
        system_prompt: Optional[str] = None,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.system_prompt = system_prompt or "You are a helpful assistant."
        self.client = httpx.AsyncClient(timeout=timeout)

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Send a chat completion request to Ollama."""
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        try:
            resp = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "success": True,
                "content": data.get("message", {}).get("content", ""),
                "model": self.model,
                "done": data.get("done", True),
                "raw": data,
            }
        except httpx.ConnectError as e:
            logger.error("Ollama connection failed", error=str(e), model=self.model)
            return {
                "success": False,
                "content": f"Ollama connection failed: {e}. Ensure `ollama serve` is running.",
                "model": self.model,
                "done": True,
            }
        except httpx.HTTPStatusError as e:
            logger.error("Ollama HTTP error", status=e.response.status_code, model=self.model)
            return {
                "success": False,
                "content": f"Ollama HTTP error {e.response.status_code}: {e.response.text}",
                "model": self.model,
                "done": True,
            }

    async def list_models(self) -> List[str]:
        """List available models on the Ollama server."""
        try:
            resp = await self.client.get(f"{self.base_url}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            return [m.get("name", "") for m in data.get("models", [])]
        except Exception as e:
            logger.error("Failed to list Ollama models", error=str(e))
            return []

    async def is_available(self) -> bool:
        """Check if Ollama server is reachable."""
        try:
            resp = await self.client.get(f"{self.base_url}/api/tags")
            return resp.status_code == 200
        except Exception:
            return False

    async def close(self):
        await self.client.aclose()
