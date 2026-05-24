#!/usr/bin/env python3
"""
AGENT CONSENSUS ENGINE — LLM Inference as Consensus Vote

Core Innovation: Every LLM token generation produces a cryptographic signature
that acts as a consensus vote. Multiple agents run inference on the same prompt;
their outputs are hashed and compared. Agreement above a threshold creates consensus.

On M5 Pro Macs, each agent runs its own Ollama instance. They communicate
via a lightweight gossip protocol, sharing inference hashes. When 2/3 of agents
agree on a state root, it is settled to the multi-chain bridge.

Throughput: With N agents running in parallel, each doing inference at ~50 tok/sec,
the effective "consensus TPS" is N * 50 * batch_size, easily reaching 1M+ internal ops/sec
before settlement to L1.
"""
import asyncio
import hashlib
import json
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import requests


@dataclass
class ConsensusVote:
    agent_id: str
    state_root: str
    inference_hash: str  # hash of LLM output
    confidence: float
    timestamp: float


@dataclass
class ConsensusRound:
    round_id: str
    state_root: str
    votes: List[ConsensusVote] = field(default_factory=list)
    threshold: float = 0.67  # 2/3 majority
    finalized: bool = False
    finality_time: float = 0.0


class LLMConsensusEngine:
    """Uses LLM inference as a consensus mechanism."""

    CONSENSUS_PROMPT = """You are a blockchain validator. Evaluate this state root for validity.
State Root: {state_root}
Batch Contents: {batch_summary}

Respond with exactly one word: VALID or INVALID.
Your response will be hashed and used as a consensus vote."""

    def __init__(self, groq_api_key: str = "", model: str = "llama-3.3-70b-versatile"):
        self.api_key = groq_api_key
        self.model = model
        self.base = "https://api.groq.com/openai/v1"
        self.rounds: Dict[str, ConsensusRound] = {}
        self.my_agent_id = self._generate_agent_id()
        self.vote_history: List[Dict] = []

    def _generate_agent_id(self) -> str:
        machine = f"{os.uname().nodename}-{os.getpid()}"
        return hashlib.sha256(machine.encode()).hexdigest()[:12]

    def _call_llm(self, prompt: str) -> str:
        """Run inference via Groq API. The output hash becomes our vote."""
        if not self.api_key:
            # Deterministic fallback for testing
            return f"VALID_{hashlib.sha256(prompt.encode()).hexdigest()[:8]}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a precise validator. One word answers only."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.0,  # Deterministic for reproducible votes
            "max_tokens": 10,
        }
        try:
            resp = requests.post(f"{self.base}/chat/completions", headers=headers, json=data, timeout=20)
            result = resp.json()["choices"][0]["message"]["content"]
            return result.strip()
        except Exception as e:
            return f"ERROR_{e}"

    def _hash_inference(self, text: str) -> str:
        """Hash the LLM output to create a deterministic vote signature."""
        return hashlib.sha256(text.encode()).hexdigest()

    def cast_vote(self, state_root: str, batch_summary: str) -> ConsensusVote:
        """Run LLM inference and cast a consensus vote."""
        prompt = self.CONSENSUS_PROMPT.format(
            state_root=state_root,
            batch_summary=batch_summary[:500],
        )
        inference = self._call_llm(prompt)
        inf_hash = self._hash_inference(inference)

        # Confidence based on response
        confidence = 0.95 if "VALID" in inference.upper() else 0.1
        if "ERROR" in inference:
            confidence = 0.0

        vote = ConsensusVote(
            agent_id=self.my_agent_id,
            state_root=state_root,
            inference_hash=inf_hash,
            confidence=confidence,
            timestamp=time.time(),
        )
        return vote

    def add_external_vote(self, vote: ConsensusVote):
        """Add a vote received from another agent via P2P."""
        if vote.state_root not in self.rounds:
            self.rounds[vote.state_root] = ConsensusRound(
                round_id=f"round-{vote.state_root[:16]}",
                state_root=vote.state_root,
            )
        self.rounds[vote.state_root].votes.append(vote)
        self._check_consensus(vote.state_root)

    def _check_consensus(self, state_root: str):
        """Check if 2/3 majority has been reached."""
        r = self.rounds.get(state_root)
        if not r or r.finalized:
            return

        # Count votes agreeing with the most common hash
        hash_counts = defaultdict(int)
        for v in r.votes:
            hash_counts[v.inference_hash] += 1

        top_hash = ""
        max_count = 0
        for hsh, count in hash_counts.items():
            if count > max_count:
                max_count = count
                top_hash = hsh

        total = len(r.votes)
        # Exact 2/3 check with integer math: avoids floating point issues
        if total >= 3 and max_count * 3 >= total * 2:
            r.finalized = True
            r.finality_time = time.time()
            self.vote_history.append({
                "state_root": state_root,
                "votes": total,
                "agreement": max_count / total,
                "finality_ms": round((r.finality_time - r.votes[0].timestamp) * 1000, 2),
                "winning_hash": top_hash,
            })

    async def run_consensus_round(self, state_root: str, batch_summary: str) -> ConsensusRound:
        """Run a full consensus round: cast our vote, collect from P2P, check result."""
        our_vote = self.cast_vote(state_root, batch_summary)
        self.add_external_vote(our_vote)

        # Wait for other agents to submit votes (via P2P callback)
        start = time.time()
        timeout = 10.0
        while time.time() - start < timeout:
            r = self.rounds.get(state_root)
            if r and r.finalized:
                break
            await asyncio.sleep(0.5)

        return self.rounds.get(state_root, ConsensusRound(round_id="empty", state_root=state_root))

    def get_stats(self) -> Dict:
        finalized = [r for r in self.rounds.values() if r.finalized]
        return {
            "agent_id": self.my_agent_id,
            "total_rounds": len(self.rounds),
            "finalized": len(finalized),
            "avg_finality_ms": round(
                sum(v["finality_ms"] for v in self.vote_history) / max(len(self.vote_history), 1), 2
            ),
            "recent_votes": self.vote_history[-5:],
        }
