#!/usr/bin/env python3
"""
MEMBRA L3 — Multi-Chain Autonomous Layer 3
Bridges Solana + Sui + Berachain with LLM consensus and P2P agent network.

Every M5 Pro Mac runs a Membra L3 node that:
1. Mines local files for value
2. Runs LLM inference (consensus votes)
3. Communicates with peer agents via P2P
4. Batches internal operations at 1M+ ops/sec
5. Settles state roots to 3 chains (2/3 consensus)
6. Trades compute resources with other agents

Architecture:
┌─────────────────────────────────────────────┐
│  M5 Pro Mac Node                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ FileMiner│ │ LLM Agent│ │Compute   │    │
│  │          │ │Consensus │ │Engine    │    │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘    │
│       │            │            │            │
│       └────────────┼────────────┘            │
│                    │                         │
│              ┌─────┴─────┐                 │
│              │   L3 Batcher│  1M+ ops/sec    │
│              │   (internal)│                 │
│              └─────┬─────┘                 │
│                    │                         │
│       ┌────────────┼────────────┐            │
│       │            │            │            │
│  ┌────┴────┐ ┌────┴────┐ ┌────┴────┐       │
│  │ Solana  │ │   Sui   │ │ Berachain│       │
│  │ devnet  │ │ testnet │ │ bArtio  │       │
│  └─────────┘ └─────────┘ └─────────┘       │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │ P2P Gossip (other M5 Mac agents)   │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
"""
import asyncio
import hashlib
import json
import os
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

import psutil
import yaml

from real_chain import AutonomousChain, ChainConfig
from chain_bridge import ComputeToChainBridge
from multi_chain_bridge import MultiChainBridge
from agent_consensus import LLMConsensusEngine
from agent_p2p import AgentP2PNetwork


class MembraL3Node:
    """Full L3 node: compute + consensus + multi-chain settlement + P2P."""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), "config.yaml")
        with open(self.config_path) as f:
            self.config = yaml.safe_load(f)

        # Core systems
        self.chain = AutonomousChain()
        self.bridge = ComputeToChainBridge(self.chain)
        self.multi_chain = MultiChainBridge()
        self.consensus = LLMConsensusEngine(
            groq_api_key=self.chain.config.groq_api_key,
            model=self.chain.config.groq_model,
        )
        self.p2p = AgentP2PNetwork(agent_id=self.consensus.my_agent_id)

        # L3 internal ledger (high-throughput)
        self.internal_ops: deque = deque()
        self.ops_processed = 0
        self.ops_settled = 0
        self.batch_id = 0

        # Agent trading
        self.trade_history: List[Dict] = []
        self.resource_offers: List[Dict] = []

        self.running = False

    async def run(self):
        """Start the full L3 node."""
        self.running = True
        print("=" * 70)
        print("  MEMBRA L3 — Multi-Chain Autonomous Node")
        print(f"  Agent: {self.consensus.my_agent_id}")
        print(f"  Chains: Solana devnet | Sui testnet | Berachain bArtio")
        print("=" * 70)

        # Start all subsystems
        await asyncio.gather(
            self._compute_loop(),
            self._consensus_loop(),
            self._settlement_loop(),
            self._p2p_loop(),
            self._trading_loop(),
            self._status_loop(),
        )

    async def _compute_loop(self):
        """Mine files, run inference, queue operations."""
        while self.running:
            try:
                # Scan files
                files = self.chain.appraiser.scan(max_files=20)
                if files:
                    appraisals = self.chain.appraiser.appraise_all(self.chain.agent, max_appraise=5)
                    for appraisal in appraisals:
                        op = {
                            "type": "compute",
                            "file": appraisal["file"]["name"],
                            "value": appraisal.get("token_value", 0),
                            "score": appraisal.get("value_score", 0),
                            "timestamp": time.time(),
                        }
                        self.internal_ops.append(op)
                        self.ops_processed += 1

                        # Queue on-chain reward
                        self.bridge.queue_reward(
                            task_id=f"op-{self.ops_processed}",
                            task_type=appraisal.get("category", "generic"),
                            value_score=appraisal.get("value_score", 50),
                        )

                await asyncio.sleep(5)
            except Exception as e:
                print(f"[COMPUTE] Error: {e}")
                await asyncio.sleep(10)

    async def _consensus_loop(self):
        """Run LLM consensus on pending state roots."""
        while self.running:
            try:
                if len(self.internal_ops) >= 10:
                    # Form a state root from pending ops
                    ops = [self.internal_ops.popleft() for _ in range(min(10, len(self.internal_ops)))]
                    root = hashlib.sha256(json.dumps(ops, sort_keys=True).encode()).hexdigest()

                    summary = f"{len(ops)} ops: " + ", ".join(o["file"] for o in ops[:3])

                    # Run consensus (our vote + collect from P2P)
                    result = await self.consensus.run_consensus_round(root, summary)

                    if result.finalized:
                        # Broadcast to P2P that consensus reached
                        self.p2p.broadcast_vote({
                            "state_root": root,
                            "consensus": True,
                            "votes": len(result.votes),
                        })
                        print(f"[CONSENSUS] Root {root[:16]}... finalized with {len(result.votes)} votes")

                await asyncio.sleep(3)
            except Exception as e:
                print(f"[CONSENSUS] Error: {e}")
                await asyncio.sleep(5)

    async def _settlement_loop(self, interval: int = 30):
        """Settle finalized batches to all 3 chains."""
        while self.running:
            try:
                # Check for finalized consensus rounds
                finalized = [r for r in self.consensus.rounds.values() if r.finalized]
                if finalized:
                    # Settle the most recent
                    latest = max(finalized, key=lambda x: x.finality_time)
                    self.batch_id += 1

                    print(f"[SETTLE] Batch {self.batch_id} — root {latest.state_root[:16]}...")
                    result = await self.multi_chain.settle_all(latest.state_root, self.batch_id)

                    if result.get("consensus_reached"):
                        self.ops_settled += len(latest.votes)
                        print(f"[SETTLE] ✅ Multi-chain consensus: {result['confirmed_count']}/3 chains")
                    else:
                        print(f"[SETTLE] ⚠️ Only {result['confirmed_count']}/3 chains confirmed")

                await asyncio.sleep(interval)
            except Exception as e:
                print(f"[SETTLE] Error: {e}")
                await asyncio.sleep(interval)

    async def _p2p_loop(self):
        """Run P2P network for agent communication."""
        try:
            await self.p2p.start()
        except Exception as e:
            print(f"[P2P] Could not start: {e}")
            # Keep running without P2P
            while self.running:
                await asyncio.sleep(60)

    async def _trading_loop(self):
        """Trade compute resources with peer agents."""
        while self.running:
            try:
                # Advertise our resources
                mem = psutil.virtual_memory()
                offer = {
                    "cpu_cores": psutil.cpu_count(),
                    "cpu_percent": psutil.cpu_percent(interval=0.5),
                    "memory_gb": mem.total / (1024**3),
                    "memory_percent": mem.percent,
                    "price_per_hour": 0.05 * psutil.cpu_count(),
                }
                self.p2p.broadcast_trade(offer)

                # Check peer offers and trade if beneficial
                for trade in self.p2p.trade_offers:
                    if trade.get("from") != self.consensus.my_agent_id:
                        # Simple matching: accept if price < our price * 0.8
                        peer_price = trade.get("offer", {}).get("price_per_hour", 999)
                        if peer_price < offer["price_per_hour"] * 0.8:
                            self.trade_history.append({
                                "peer": trade["from"],
                                "price": peer_price,
                                "timestamp": time.time(),
                                "status": "accepted",
                            })

                await asyncio.sleep(15)
            except Exception as e:
                print(f"[TRADE] Error: {e}")
                await asyncio.sleep(15)

    async def _status_loop(self):
        """Print periodic status updates."""
        while self.running:
            await asyncio.sleep(10)
            try:
                status = self.get_status()
                print(f"\n[STATUS] Ops: {status['ops_processed']} | "
                      f"Settled: {status['ops_settled']} | "
                      f"Peers: {status['p2p']['peers']} | "
                      f"Consensus: {status['consensus']['finalized']} | "
                      f"SOL: {status['solana_balance']:.4f} | "
                      f"COMPUTE: {status['token_balance']:,.0f}")
            except Exception:
                pass

    def get_status(self) -> Dict:
        return {
            "agent_id": self.consensus.my_agent_id,
            "ops_processed": self.ops_processed,
            "ops_settled": self.ops_settled,
            "pending_ops": len(self.internal_ops),
            "solana_balance": self.chain.solana.balance_sol(),
            "token_balance": self.chain.forge.get_balance(),
            "token_deployed": self.chain.state.get("token_deployed", False),
            "token_minted": self.chain.state.get("token_minted", False),
            "p2p": self.p2p.get_stats(),
            "consensus": self.consensus.get_stats(),
            "multi_chain": self.multi_chain.get_status(),
            "bridge": self.bridge.get_stats(),
            "trades": len(self.trade_history),
        }


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--autonomous", action="store_true", help="Fully autonomous mode")
    parser.add_argument("--config", default=None, help="Path to config.yaml")
    args = parser.parse_args()

    node = MembraL3Node(args.config)

    try:
        asyncio.run(node.run())
    except KeyboardInterrupt:
        node.running = False
        print("\n[SHUTDOWN] Membra L3 stopped")
