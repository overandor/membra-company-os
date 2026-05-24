#!/usr/bin/env python3
"""
Chain Bridge — Connects Mac Compute Node to Real Solana Chain
Compute tasks earn real COMPUTE tokens on Solana devnet.
"""
import asyncio
import json
import os
import time
from typing import Dict, Optional

from real_chain import AutonomousChain, ChainConfig, RealSolanaClient, TokenForge


class ComputeToChainBridge:
    """Bridges compute task completion to real on-chain token rewards."""

    def __init__(self, chain: AutonomousChain):
        self.chain = chain
        self.pending_rewards: list = []
        self.total_rewarded = 0.0
        self.reward_log: list = []
        self.state_file = os.path.expanduser("~/.mac_compute_node/rewards.json")
        self._load()

    def _load(self):
        if os.path.exists(self.state_file):
            with open(self.state_file) as f:
                state = json.load(f)
                self.total_rewarded = state.get("total", 0.0)
                self.reward_log = state.get("log", [])

    def _save(self):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump({"total": self.total_rewarded, "log": self.reward_log[-500:]}, f)

    def queue_reward(self, task_id: str, task_type: str, value_score: float, worker_node: str = "local"):
        """Queue a compute reward to be settled on-chain."""
        amount = max(0.001, value_score * 0.001)  # Base reward + score multiplier
        self.pending_rewards.append({
            "task_id": task_id,
            "task_type": task_type,
            "amount": amount,
            "worker": worker_node,
            "timestamp": time.time(),
        })

    async def settle_loop(self, interval: int = 30):
        """Periodically settle pending rewards as batched on-chain transactions."""
        while True:
            if self.pending_rewards:
                await self._settle_batch()
            await asyncio.sleep(interval)

    async def _settle_batch(self):
        """Settle a batch of rewards via the chain's batcher."""
        batch = self.pending_rewards[:50]
        self.pending_rewards = self.pending_rewards[50:]

        total = sum(r["amount"] for r in batch)

        # Enqueue each reward as a chain operation
        for reward in batch:
            self.chain.batcher.enqueue("compute_reward", reward)
            self.total_rewarded += reward["amount"]
            self.reward_log.append(reward)

        print(f"[BRIDGE] Queued {len(batch)} rewards = {total:.4f} {self.chain.config.token_symbol}")
        self._save()

    def get_stats(self) -> Dict:
        return {
            "pending_rewards": len(self.pending_rewards),
            "total_rewarded": round(self.total_rewarded, 6),
            "currency": self.chain.config.token_symbol,
            "recent_rewards": self.reward_log[-10:],
        }


class IntegratedNode:
    """Fully integrated Mac Compute Node + Real Chain."""

    def __init__(self):
        self.chain = AutonomousChain()
        self.bridge = ComputeToChainBridge(self.chain)

    async def run(self):
        """Run both compute node and chain in parallel."""
        print("[INTEGRATED] Starting Mac Compute Node with Real Chain...")

        # Start chain batcher
        asyncio.create_task(self.chain.batcher.run())

        # Start reward settlement
        asyncio.create_task(self.bridge.settle_loop())

        # Start autonomous chain loop
        asyncio.create_task(self.chain.run_autonomous())

        # Keep alive
        while True:
            await asyncio.sleep(60)
            print(f"[LIVE] Chain: {self.chain.batcher.get_stats()}")
            print(f"[LIVE] Bridge: {self.bridge.get_stats()}")


if __name__ == "__main__":
    node = IntegratedNode()
    asyncio.run(node.run())
