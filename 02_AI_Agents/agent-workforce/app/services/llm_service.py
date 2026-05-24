import asyncio
import time
from typing import Any, Dict, List, Optional
import httpx
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("llm_service")

class LLMService:
    def __init__(self):
        self.openai_key = settings.openai_api_key
        self.anthropic_key = settings.anthropic_api_key
        self.groq_key = settings.groq_api_key
        self.client = httpx.AsyncClient(timeout=60.0)

    async def generate(
        self,
        prompt: str,
        model: str = "gpt-4o",
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> Dict[str, Any]:
        start = time.time()
        provider = self._detect_provider(model)
        try:
            if provider == "openai":
                result = await self._openai_generate(prompt, model, system, temperature, max_tokens, json_mode)
            elif provider == "anthropic":
                result = await self._anthropic_generate(prompt, model, system, temperature, max_tokens)
            elif provider == "groq":
                result = await self._groq_generate(prompt, model, system, temperature, max_tokens, json_mode)
            else:
                result = await self._openai_generate(prompt, model, system, temperature, max_tokens, json_mode)
            result["elapsed_ms"] = (time.time() - start) * 1000
            return result
        except Exception as e:
            logger.error("llm_generate_failed", provider=provider, model=model, error=str(e))
            raise

    def _detect_provider(self, model: str) -> str:
        if model.startswith("claude"):
            return "anthropic"
        if any(x in model for x in ["llama", "mixtral", "gemma", "deepseek"]):
            return "groq"
        if model.startswith("gpt") or model.startswith("o1"):
            return "openai"
        return "openai"

    async def _openai_generate(self, prompt, model, system, temperature, max_tokens, json_mode):
        headers = {"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"}
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        resp = await self.client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return {
            "text": data["choices"][0]["message"]["content"],
            "tokens_used": data["usage"]["total_tokens"],
            "model": model,
            "provider": "openai",
        }

    async def _anthropic_generate(self, prompt, model, system, temperature, max_tokens):
        headers = {
            "x-api-key": self.anthropic_key or "",
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            payload["system"] = system
        resp = await self.client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return {
            "text": data["content"][0]["text"],
            "tokens_used": data["usage"]["input_tokens"] + data["usage"]["output_tokens"],
            "model": model,
            "provider": "anthropic",
        }

    async def _groq_generate(self, prompt, model, system, temperature, max_tokens, json_mode):
        headers = {"Authorization": f"Bearer {self.groq_key}", "Content-Type": "application/json"}
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        resp = await self.client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return {
            "text": data["choices"][0]["message"]["content"],
            "tokens_used": data["usage"]["total_tokens"],
            "model": model,
            "provider": "groq",
        }

    async def embed(self, text: str) -> List[float]:
        headers = {"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"}
        payload = {"model": "text-embedding-3-small", "input": text}
        resp = await self.client.post("https://api.openai.com/v1/embeddings", headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()["data"][0]["embedding"]

llm_service = LLMService()
