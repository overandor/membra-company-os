#!/usr/bin/env python3
"""
Python LLM Adapter — drop this into any Python project.
Provides async/sync LLM calls via local Ollama.
"""

import json
import os
import urllib.request
from typing import Dict, List, Optional

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")


class LLMClient:
    """Local LLM client for Python projects. No API keys."""

    def __init__(self, host: str = OLLAMA_HOST, default_model: str = "llama3.2:1b"):
        self.host = host.rstrip("/")
        self.default_model = default_model

    def generate(self, prompt: str, model: Optional[str] = None, system: str = "", temperature: float = 0.7, max_tokens: int = 400) -> str:
        model = model or self.default_model
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{self.host}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read())
            return result.get("response", "")

    def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
        model = model or self.default_model
        payload = {"model": model, "messages": messages, "stream": False}
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{self.host}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read())
            return result.get("message", {}).get("content", "")

    def embed(self, text: str, model: str = "nomic-embed-text") -> List[float]:
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

    def code_review(self, code: str, language: str = "python") -> str:
        system = f"You are a senior {language} engineer. Review the code for bugs, style, performance, and security."
        prompt = f"Review this {language} code:\n\n```\n{code}\n```\n\nGive concise bullet points."
        return self.generate(prompt, system=system, temperature=0.3, max_tokens=600)

    def generate_tests(self, code: str, language: str = "python") -> str:
        system = f"You are a test engineer. Generate comprehensive unit tests."
        prompt = f"Generate unit tests for this {language} code:\n\n```\n{code}\n```"
        return self.generate(prompt, system=system, temperature=0.2, max_tokens=800)

    def explain_code(self, code: str) -> str:
        prompt = f"Explain this code step by step:\n\n```\n{code}\n```"
        return self.generate(prompt, system="You explain code clearly.", temperature=0.3, max_tokens=500)


# Singleton for easy import
llm = LLMClient()

if __name__ == "__main__":
    # Quick test
    print("Testing local LLM...")
    print(llm.generate("What is 2+2?", max_tokens=50))
