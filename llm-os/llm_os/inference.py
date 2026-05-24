"""Inference — LLM inference bridges for code generation and analysis.

Provides a unified interface to multiple LLM providers:
- GroqBridge: Fast inference via Groq Cloud (GROQ_API_KEY)
- OpenRouterBridge: Multi-model access via OpenRouter (OPENROUTER_API_KEY)
- GeminiBridge: Google Gemini API (GEMINI_API_KEY)
- StubBridge: Deterministic fallback when no API keys are available

All bridges implement the same interface so the rest of the OS
can generate code, analyse signals, and reason about tasks without
caring which backend is live.
"""

import json
import os
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class InferenceResult:
    """Result from an LLM inference call."""
    text: str
    model: str
    provider: str
    tokens_used: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class _BaseBridge:
    """Common interface every inference bridge must implement."""

    provider: str = "base"

    def is_available(self) -> bool:
        raise NotImplementedError

    def generate(self, prompt: str, system_prompt: str = "",
                 max_tokens: int = 2048, temperature: float = 0.7) -> InferenceResult:
        raise NotImplementedError

    # Convenience -------------------------------------------------------
    def _post_json(self, url: str, headers: dict, payload: dict,
                   timeout: int = 30) -> dict:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            body = exc.read().decode() if exc.fp else ""
            raise RuntimeError(f"HTTP {exc.code}: {body}") from exc


class GroqBridge(_BaseBridge):
    """Groq Cloud inference — very fast, good for code gen."""

    provider = "groq"
    API_URL = "https://api.groq.com/openai/v1/chat/completions"
    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    COST_PER_1K_TOKENS = 0.00059

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, system_prompt: str = "",
                 max_tokens: int = 2048, temperature: float = 0.7) -> InferenceResult:
        if not self.is_available():
            return InferenceResult(text="", model=self.DEFAULT_MODEL,
                                   provider=self.provider, success=False,
                                   error="GROQ_API_KEY not set")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        t0 = time.time()
        try:
            resp = self._post_json(
                self.API_URL,
                {"Authorization": f"Bearer {self.api_key}",
                 "Content-Type": "application/json"},
                {"model": self.DEFAULT_MODEL, "messages": messages,
                 "max_tokens": max_tokens, "temperature": temperature},
            )
        except Exception as exc:
            return InferenceResult(text="", model=self.DEFAULT_MODEL,
                                   provider=self.provider, success=False,
                                   error=str(exc),
                                   latency_ms=(time.time() - t0) * 1000)

        latency = (time.time() - t0) * 1000
        text = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = resp.get("usage", {})
        tokens = usage.get("total_tokens", 0)
        cost = (tokens / 1000) * self.COST_PER_1K_TOKENS
        return InferenceResult(text=text, model=self.DEFAULT_MODEL,
                               provider=self.provider, tokens_used=tokens,
                               cost_usd=cost, latency_ms=latency,
                               metadata={"usage": usage})


class OpenRouterBridge(_BaseBridge):
    """OpenRouter — routes to many models (Claude, GPT-4, Llama, etc.)."""

    provider = "openrouter"
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct"
    COST_PER_1K_TOKENS = 0.0008

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, system_prompt: str = "",
                 max_tokens: int = 2048, temperature: float = 0.7) -> InferenceResult:
        if not self.is_available():
            return InferenceResult(text="", model=self.DEFAULT_MODEL,
                                   provider=self.provider, success=False,
                                   error="OPENROUTER_API_KEY not set")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        t0 = time.time()
        try:
            resp = self._post_json(
                self.API_URL,
                {"Authorization": f"Bearer {self.api_key}",
                 "Content-Type": "application/json",
                 "HTTP-Referer": "https://membra.ai",
                 "X-Title": "MEMBRA LLM OS"},
                {"model": self.DEFAULT_MODEL, "messages": messages,
                 "max_tokens": max_tokens, "temperature": temperature},
            )
        except Exception as exc:
            return InferenceResult(text="", model=self.DEFAULT_MODEL,
                                   provider=self.provider, success=False,
                                   error=str(exc),
                                   latency_ms=(time.time() - t0) * 1000)

        latency = (time.time() - t0) * 1000
        text = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = resp.get("usage", {})
        tokens = usage.get("total_tokens", 0)
        cost = (tokens / 1000) * self.COST_PER_1K_TOKENS
        return InferenceResult(text=text, model=self.DEFAULT_MODEL,
                               provider=self.provider, tokens_used=tokens,
                               cost_usd=cost, latency_ms=latency,
                               metadata={"usage": usage})


class GeminiBridge(_BaseBridge):
    """Google Gemini API bridge."""

    provider = "gemini"
    DEFAULT_MODEL = "gemini-2.0-flash"
    COST_PER_1K_TOKENS = 0.000075

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")

    @property
    def _api_url(self) -> str:
        return (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.DEFAULT_MODEL}:generateContent?key={self.api_key}"
        )

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, system_prompt: str = "",
                 max_tokens: int = 2048, temperature: float = 0.7) -> InferenceResult:
        if not self.is_available():
            return InferenceResult(text="", model=self.DEFAULT_MODEL,
                                   provider=self.provider, success=False,
                                   error="GEMINI_API_KEY not set")
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens,
                                 "temperature": temperature},
        }
        t0 = time.time()
        try:
            resp = self._post_json(
                self._api_url,
                {"Content-Type": "application/json"},
                payload,
            )
        except Exception as exc:
            return InferenceResult(text="", model=self.DEFAULT_MODEL,
                                   provider=self.provider, success=False,
                                   error=str(exc),
                                   latency_ms=(time.time() - t0) * 1000)

        latency = (time.time() - t0) * 1000
        candidates = resp.get("candidates", [])
        text = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            text = parts[0].get("text", "") if parts else ""
        usage = resp.get("usageMetadata", {})
        tokens = usage.get("totalTokenCount", 0)
        cost = (tokens / 1000) * self.COST_PER_1K_TOKENS
        return InferenceResult(text=text, model=self.DEFAULT_MODEL,
                               provider=self.provider, tokens_used=tokens,
                               cost_usd=cost, latency_ms=latency,
                               metadata={"usage": usage})


class StubBridge(_BaseBridge):
    """Deterministic fallback — returns template-based code with zero cost."""

    provider = "stub"

    def is_available(self) -> bool:
        return True

    def generate(self, prompt: str, system_prompt: str = "",
                 max_tokens: int = 2048, temperature: float = 0.7) -> InferenceResult:
        text = self._template_response(prompt)
        return InferenceResult(text=text, model="stub-v1",
                               provider=self.provider, tokens_used=0,
                               cost_usd=0.0, latency_ms=0.0)

    @staticmethod
    def _template_response(prompt: str) -> str:
        lower = prompt.lower()
        if "trading" in lower or "market" in lower:
            return _STUB_TRADING_CODE
        if "api" in lower or "fastapi" in lower:
            return _STUB_API_CODE
        if "dashboard" in lower or "web" in lower:
            return _STUB_DASHBOARD_CODE
        return _STUB_GENERIC_CODE


# ---------------------------------------------------------------------------
# Public helpers used by system_builder and other modules
# ---------------------------------------------------------------------------

_BRIDGE_PRIORITY: List[type] = [GroqBridge, OpenRouterBridge, GeminiBridge, StubBridge]


def get_inference_bridge() -> _BaseBridge:
    """Return the best available inference bridge."""
    for cls in _BRIDGE_PRIORITY:
        bridge = cls()
        if bridge.is_available():
            return bridge
    return StubBridge()


def generate_code_with_llm(prompt: str, target_type: str = "generic") -> dict:
    """High-level helper: generate code files for a given prompt.

    Returns ``{"success": bool, "files": {name: content}, "cost_usd": float}``.
    """
    bridge = get_inference_bridge()
    system_prompt = (
        "You are a senior software engineer. Generate clean, production-ready code. "
        "Return ONLY code, no explanations. Use ```filename.ext blocks to separate files."
    )
    result = bridge.generate(prompt, system_prompt=system_prompt)
    if not result.success:
        return {"success": False, "files": {}, "cost_usd": result.cost_usd,
                "error": result.error}

    files = _parse_code_blocks(result.text, target_type)
    if not files:
        files = {f"main.{'py' if 'python' in target_type.lower() else 'js'}": result.text}

    return {"success": True, "files": files, "cost_usd": result.cost_usd,
            "model": result.model, "provider": result.provider}


def _parse_code_blocks(text: str, target_type: str) -> Dict[str, str]:
    """Extract ``filename: content`` pairs from markdown-style code blocks."""
    files: Dict[str, str] = {}
    lines = text.split("\n")
    current_file: Optional[str] = None
    current_content: List[str] = []

    for line in lines:
        if line.startswith("```") and current_file is None:
            rest = line[3:].strip()
            if rest and not rest.startswith("{"):
                current_file = rest.split()[0] if rest else None
                current_content = []
        elif line.strip() == "```" and current_file is not None:
            files[current_file] = "\n".join(current_content)
            current_file = None
            current_content = []
        elif current_file is not None:
            current_content.append(line)

    return files


# ---------------------------------------------------------------------------
# Stub templates
# ---------------------------------------------------------------------------

_STUB_TRADING_CODE = '''\
"""Auto-generated trading bot stub."""
import time

class TradingBot:
    def __init__(self, symbol="BTC/USDT", dry_run=True):
        self.symbol = symbol
        self.dry_run = dry_run
        self.pnl = 0.0

    def fetch_price(self):
        return 50000.0 + (time.time() % 1000)

    def decide(self, price):
        return "hold"

    def run_once(self):
        price = self.fetch_price()
        action = self.decide(price)
        return {"symbol": self.symbol, "price": price, "action": action, "pnl": self.pnl}

if __name__ == "__main__":
    bot = TradingBot()
    print(bot.run_once())
'''

_STUB_API_CODE = '''\
"""Auto-generated FastAPI service stub."""
from fastapi import FastAPI

app = FastAPI(title="Generated API")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "Service is running"}
'''

_STUB_DASHBOARD_CODE = '''\
<!DOCTYPE html>
<html><head><title>Dashboard</title></head>
<body>
<h1>Dashboard</h1>
<div id="status">Loading…</div>
<script>
fetch("/state").then(r=>r.json()).then(d=>{
  document.getElementById("status").textContent=JSON.stringify(d,null,2);
});
</script>
</body></html>
'''

_STUB_GENERIC_CODE = '''\
"""Auto-generated Python module."""

def main():
    print("Module running")
    return {"status": "ok"}

if __name__ == "__main__":
    main()
'''
