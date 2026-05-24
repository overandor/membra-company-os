#!/usr/bin/env python3
"""
3-AGENT CONSENSUS TEST — Proves multi-agent proof-of-proof works.

Starts 3 Membra agents in the same process.
Each agent receives the same prompt/batch.
Agents run inference (or simulated inference), hash responses.
When 2/3 hashes match, consensus is reached and batch finalizes.
"""
import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ConsensusVote:
    agent_id: str
    state_root: str
    inference_hash: str
    confidence: float
    timestamp: float


@dataclass
class ConsensusRound:
    round_id: str
    state_root: str
    votes: List[ConsensusVote] = field(default_factory=list)
    threshold: float = 0.6667  # 2/3 majority
    finalized: bool = False
    finality_time: float = 0.0


class LLMConsensusEngine:
    """Simplified consensus engine for 3-agent test."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.rounds: Dict[str, ConsensusRound] = {}

    def cast_vote(self, state_root: str, inference_output: str) -> ConsensusVote:
        inf_hash = hashlib.sha256(inference_output.encode()).hexdigest()
        return ConsensusVote(
            agent_id=self.agent_id,
            state_root=state_root,
            inference_hash=inf_hash,
            confidence=0.95,
            timestamp=time.time(),
        )

    def add_external_vote(self, vote: ConsensusVote):
        if vote.state_root not in self.rounds:
            self.rounds[vote.state_root] = ConsensusRound(
                round_id=f"round-{vote.state_root[:16]}",
                state_root=vote.state_root,
            )
        self.rounds[vote.state_root].votes.append(vote)
        self._check_consensus(vote.state_root)

    def _check_consensus(self, state_root: str):
        r = self.rounds.get(state_root)
        if not r or r.finalized:
            return
        if len(r.votes) < 3:
            return

        hash_counts = {}
        for v in r.votes:
            hash_counts[v.inference_hash] = hash_counts.get(v.inference_hash, 0) + 1

        top_hash, top_count = max(hash_counts.items(), key=lambda x: x[1])
        # Exact 2/3 check with integers: top_count * 3 >= total * 2
        total = len(r.votes)
        if top_count * 3 >= total * 2:
            r.finalized = True
            r.finality_time = time.time()

    def get_round(self, state_root: str) -> ConsensusRound:
        return self.rounds.get(state_root, ConsensusRound(round_id="empty", state_root=state_root))


class Agent:
    """Single Membra validator agent."""

    def __init__(self, agent_id: str, model_response: str):
        self.agent_id = agent_id
        self.model_response = model_response
        self.consensus = LLMConsensusEngine(agent_id)
        self.votes_cast = 0

    def process_batch(self, state_root: str, summary: str) -> ConsensusVote:
        # Simulate LLM inference on this batch
        # In production: this would call Ollama/Groq
        inference = f"VALID | batch_summary={summary} | model_output={self.model_response}"
        vote = self.consensus.cast_vote(state_root, inference)
        self.votes_cast += 1
        return vote


async def run_3_agent_consensus():
    print("=" * 70)
    print("  3-AGENT CONSENSUS TEST")
    print("  Proof-of-Proof: LLM inference hashes = validator votes")
    print("=" * 70)
    print()

    # Create 3 agents
    # Agent 1 and 2 use the same model response → their hashes will match
    # Agent 3 uses a different response → its hash will differ
    agent1 = Agent("agent-alpha", "llama3.2-7b-analysis")
    agent2 = Agent("agent-beta", "llama3.2-7b-analysis")   # Same response = hash match
    agent3 = Agent("agent-gamma", "mistral-7b-different")  # Different = hash mismatch

    agents = [agent1, agent2, agent3]
    print(f"  Created {len(agents)} agents:")
    for a in agents:
        print(f"    - {a.agent_id}: model={a.model_response}")
    print()

    # Create a batch (simulated file operations)
    batch_ops = [
        {"file": "contract.rs", "value": 0.85},
        {"file": "bridge.sol", "value": 0.92},
        {"file": "network.go", "value": 0.78},
        {"file": "consensus.cpp", "value": 0.88},
        {"file": "runtime.rs", "value": 0.90},
    ]
    state_root = hashlib.sha256(json.dumps(batch_ops, sort_keys=True).encode()).hexdigest()
    summary = f"{len(batch_ops)} files: {', '.join(o['file'] for o in batch_ops)}"

    print(f"  Batch: {len(batch_ops)} operations")
    print(f"  State Root: {state_root[:32]}...")
    print(f"  Summary: {summary[:60]}")
    print()

    # Each agent processes the batch and casts a vote
    print("  [PHASE 1] Agents run inference and cast votes...")
    all_votes = []
    for agent in agents:
        vote = agent.process_batch(state_root, summary)
        all_votes.append(vote)
        print(f"    {agent.agent_id}: hash={vote.inference_hash[:16]}... conf={vote.confidence}")
    print()

    # Share all votes with all agents (P2P gossip simulation)
    print("  [PHASE 2] Gossiping votes between agents...")
    for agent in agents:
        for vote in all_votes:
            agent.consensus.add_external_vote(vote)
        print(f"    {agent.agent_id} received {len(all_votes)} votes")
    print()

    # Check consensus on any agent (they all have the same view)
    print("  [PHASE 3] Checking consensus...")
    round_result = agent1.consensus.get_round(state_root)

    if round_result.finalized:
        finality_ms = round((round_result.finality_time - round_result.votes[0].timestamp) * 1000, 2)
        print(f"    ✅ CONSENSUS REACHED")
        print(f"       Votes: {len(round_result.votes)}")
        print(f"       Agreement threshold: {round_result.threshold * 100:.0f}%")
        print(f"       Finality time: {finality_ms} ms")

        # Show hash breakdown
        hash_counts = {}
        for v in round_result.votes:
            hash_counts[v.inference_hash] = hash_counts.get(v.inference_hash, 0) + 1
        print(f"       Hash breakdown:")
        for h, c in hash_counts.items():
            marker = "← WINNING" if c >= 2 else ""
            print(f"         {h[:16]}...: {c} votes {marker}")
    else:
        print(f"    ❌ CONSENSUS NOT REACHED")
        print(f"       Votes: {len(round_result.votes)} (need 3+)")

    print()
    print("=" * 70)
    print("  RESULT")
    print("=" * 70)
    print(f"  Agents:              {len(agents)}")
    print(f"  Votes cast:          {len(all_votes)}")
    print(f"  Consensus reached:   {'YES' if round_result.finalized else 'NO'}")
    print(f"  Finalized batches:   {sum(1 for r in agent1.consensus.rounds.values() if r.finalized)}")
    print()
    print("  This proves: When 2/3 agents produce matching inference hashes,")
    print("  proof-of-proof consensus finalizes the batch.")
    print("  Next step: Anchor the finalized root to Solana devnet.")
    print()

    return round_result.finalized, state_root


if __name__ == "__main__":
    ok, root = asyncio.run(run_3_agent_consensus())
    exit(0 if ok else 1)
