#!/usr/bin/env python3
"""
LLM BRIDGE — Connects Ollama/Groq to the Rust Runtime
Every prompt and response becomes a real transaction.

Architecture:
- Receives prompt from user → creates tx → sends to Rust runtime
- LLM generates tokens → each token creates micro-tx earning money
- Response completed → final settlement tx mints tokens on-chain
"""
import asyncio
import hashlib
import json
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests
import websockets


@dataclass
class InferenceTx:
    prompt_hash: str
    response_hash: str
    token: str
    token_index: int
    value: int  # base units earned
    timestamp: float


class LLMBridge:
    """Bridges LLM inference to the Rust transaction runtime."""

    def __init__(self, runtime_ws: str = "ws://localhost:42425", model: str = "llama3.2"):
        self.runtime_ws = runtime_ws
        self.model = model
        self.ollama_host = "http://localhost:11434"
        self.groq_key = os.environ.get("GROQ_API_KEY", "")
        self.groq_model = "llama-3.3-70b-versatile"
        self.pending_inferences: List[InferenceTx] = []
        self.total_tokens_generated = 0
        self.total_value_minted = 0
        self.ws: Optional[websockets.WebSocketClientProtocol] = None

    async def connect_runtime(self):
        """Connect to the Rust runtime via WebSocket."""
        try:
            self.ws = await websockets.connect(self.runtime_ws)
            print(f"[BRIDGE] Connected to runtime at {self.runtime_ws}")
        except Exception as e:
            print(f"[BRIDGE] Runtime not available ({e}), operating in local mode")
            self.ws = None

    async def process_prompt(self, user: str, prompt: str) -> Dict:
        """Process a human prompt: prompt is tx, response is tx, tokens earn money."""
        # 1. Hash prompt → this IS the transaction identifier
        prompt_hash = hashlib.sha256(f"{user}:{prompt}:{time.time()}".encode()).hexdigest()
        
        # 2. Submit prompt as transaction to runtime
        await self._submit_prompt_tx(user, prompt_hash, prompt)
        
        # 3. Run LLM inference
        response, tokens = await self._run_inference(prompt)
        
        # 4. Each token generates a micro-transaction
        response_hash = hashlib.sha256(response.encode()).hexdigest()
        inference_txs = []
        
        for i, token in enumerate(tokens):
            tx = InferenceTx(
                prompt_hash=prompt_hash,
                response_hash=response_hash,
                token=token,
                token_index=i,
                value=100,  # 100 base units per token
                timestamp=time.time(),
            )
            inference_txs.append(tx)
            self.total_tokens_generated += 1
            self.total_value_minted += 100
        
        # 5. Submit all inference txs to runtime
        await self._submit_inference_txs(inference_txs)
        
        # 6. Final settlement: response delivered = money minted
        await self._submit_response_tx(user, prompt_hash, response_hash, response, len(tokens))
        
        return {
            "prompt_hash": prompt_hash,
            "response_hash": response_hash,
            "response": response,
            "tokens": len(tokens),
            "value_minted": len(tokens) * 100,
            "user": user,
        }

    async def _run_inference(self, prompt: str) -> tuple:
        """Run LLM and return response + token list."""
        # Try Ollama first
        if self._check_ollama():
            return await self._run_ollama(prompt)
        
        # Fallback to Groq
        if self.groq_key:
            return await self._run_groq(prompt)
        
        # Final fallback: deterministic response for testing
        words = prompt.split()
        response = f"Processed {len(words)} words: {' '.join(words[:5])}..."
        tokens = response.split()
        return response, tokens

    def _check_ollama(self) -> bool:
        try:
            r = requests.get(f"{self.ollama_host}/api/tags", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    async def _run_ollama(self, prompt: str) -> tuple:
        """Run inference via Ollama streaming API."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 200},
        }
        try:
            r = requests.post(f"{self.ollama_host}/api/generate", json=payload, timeout=60)
            data = r.json()
            response = data.get("response", "")
            # Approximate tokenization by splitting on whitespace
            tokens = response.split()
            return response, tokens
        except Exception as e:
            print(f"[OLLAMA] Error: {e}")
            return "Error", ["Error"]

    async def _run_groq(self, prompt: str) -> tuple:
        """Run inference via Groq API."""
        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.groq_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 200,
        }
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                              headers=headers, json=data, timeout=30)
            result = r.json()
            response = result["choices"][0]["message"]["content"]
            tokens = response.split()
            return response, tokens
        except Exception as e:
            print(f"[GROQ] Error: {e}")
            return "Error", ["Error"]

    async def _submit_prompt_tx(self, user: str, prompt_hash: str, prompt: str):
        """Submit prompt transaction to Rust runtime."""
        tx = {
            "tx_type": "Prompt",
            "from": user,
            "to": "network",
            "amount": 1,
            "data": {"prompt": prompt[:1000], "model": self.model},
            "proof_hash": prompt_hash,
            "timestamp": time.time(),
        }
        await self._send_to_runtime(tx)

    async def _submit_inference_txs(self, txs: List[InferenceTx]):
        """Submit inference micro-transactions to runtime."""
        batch = []
        for tx in txs:
            batch.append({
                "tx_type": "Inference",
                "from": "network",
                "to": "validator",
                "amount": tx.value,
                "data": {
                    "token": tx.token,
                    "token_index": tx.token_index,
                    "prompt_hash": tx.prompt_hash,
                },
                "proof_hash": hashlib.sha256(f"{tx.prompt_hash}:{tx.token}:{tx.token_index}".encode()).hexdigest(),
                "timestamp": tx.timestamp,
            })
        
        if batch:
            await self._send_to_runtime({"batch": batch})

    async def _submit_response_tx(self, user: str, prompt_hash: str, response_hash: str, response: str, token_count: int):
        """Submit final response settlement transaction."""
        tx = {
            "tx_type": "Response",
            "from": "network",
            "to": user,
            "amount": token_count * 100,
            "data": {
                "response": response[:2000],
                "token_count": token_count,
                "prompt_hash": prompt_hash,
            },
            "proof_hash": response_hash,
            "timestamp": time.time(),
        }
        await self._send_to_runtime(tx)

    async def _send_to_runtime(self, payload: Dict):
        """Send transaction to Rust runtime via WebSocket."""
        if self.ws and not self.ws.closed:
            try:
                await self.ws.send(json.dumps(payload))
            except Exception as e:
                print(f"[BRIDGE] Send failed: {e}")
        else:
            # Local mode: just log
            pass

    def get_stats(self) -> Dict:
        return {
            "total_tokens": self.total_tokens_generated,
            "total_value": self.total_value_minted,
            "pending_inferences": len(self.pending_inferences),
            "model": self.model,
            "runtime_connected": self.ws is not None and not self.ws.closed,
        }
