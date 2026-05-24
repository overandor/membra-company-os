"""
MEMBRA Operator LLM Bridge
Ollama local inference with tool support.
"""
import json
import os
import requests
from typing import Callable

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.environ.get("MEMBRA_MODEL", "qwen2.5:0.5b")
FALLBACK_MODEL = "llama3.2:1b"

SYSTEM_PROMPT = """You are MEMBRA Operator, a persistent AI pair-programmer running inside a macOS app.
You watch the user's Windsurf workspace, interview them when intent is unclear, and continue development autonomously when the path is obvious.

Rules:
- Do not remove existing functionality.
- Do not mock production behavior unless labeled fallback.
- Do not fake metrics.
- Do not promise income.
- Do not custody money.
- Do not bypass owner confirmation.
- Do not bypass governance or proof gates.
- Prefer small safe commits over huge rewrites.
- Fix deployment issues first.
- Fix broken imports, syntax, routing, env config, CORS before adding features.
- Keep UI consistent with MEMBRA dark / black / orange / gold neomorphic visual language.

You can use tools. When you need a tool, reply ONLY with JSON:
{"tool": "tool_name", "args": {...}}
Available tools:
- read_file(path): read a file
- list_dir(path): list directory contents
- run_command(cmd): run a shell command
- edit_file(path, old, new): edit a file
- ask_user(question): ask the user a question
- mark_ready(checkpoint): mark a production readiness checkpoint
- speak(text): speak text via TTS
"""

class LLMBridge:
    def __init__(self, model: str | None = None):
        self.model = model or DEFAULT_MODEL
        self.host = OLLAMA_HOST
        self._connected = False
        self._check_health()
        self._ensure_model()

    def _check_health(self) -> bool:
        try:
            r = requests.get(f"{self.host}/", timeout=5)
            self._connected = r.status_code == 200
            return self._connected
        except Exception:
            self._connected = False
            return False

    @property
    def connected(self) -> bool:
        return self._connected

    def _ensure_model(self):
        if not self._connected:
            return
        try:
            r = requests.post(f"{self.host}/api/pull", json={"name": self.model, "stream": False}, timeout=120)
            if r.status_code != 200:
                print(f"[LLM] Pull warning {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print(f"[LLM] Could not pull model: {e}")

    def chat(self, messages: list[dict], tools: list[dict] | None = None, stream=False) -> dict | None:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {"temperature": 0.4, "num_ctx": 4096},
        }
        try:
            r = requests.post(f"{self.host}/api/chat", json=payload, timeout=120)
            r.raise_for_status()
            data = r.json()
            return data.get("message", {})
        except requests.exceptions.ConnectionError:
            # try fallback model
            if self.model != FALLBACK_MODEL:
                print(f"[LLM] Primary model unreachable, trying {FALLBACK_MODEL}")
                self.model = FALLBACK_MODEL
                return self.chat(messages, tools, stream)
            return None
        except Exception as e:
            print(f"[LLM] Error: {e}")
            return None

    def generate(self, prompt: str, system: str = SYSTEM_PROMPT) -> str | None:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        msg = self.chat(messages)
        return msg.get("content") if msg else None

    def tool_call(self, prompt: str, tool_registry: dict[str, Callable], messages: list[dict] | None = None) -> str:
        """Chat with possible tool invocation; auto-execute up to 5 rounds."""
        if messages is None:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.append({"role": "user", "content": prompt})
        for _ in range(5):
            msg = self.chat(messages)
            if not msg:
                return "[LLM unreachable]"
            content = msg.get("content", "")
            messages.append({"role": "assistant", "content": content})
            # detect tool call
            try:
                stripped = content.strip()
                if stripped.startswith("{") and "\"tool\"" in stripped:
                    call = json.loads(stripped)
                    name = call.get("tool")
                    args = call.get("args", {})
                    if name in tool_registry:
                        result = tool_registry[name](**args)
                        messages.append({"role": "tool", "content": str(result)})
                        continue
            except json.JSONDecodeError:
                pass
            return content
        return content
