#!/usr/bin/env python3
"""
Solana L2 Rollup Simulation for Mac Compute Node
Achieves high throughput via batching and parallel transaction processing.
"""
import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import deque


@dataclass
class L2Transaction:
    tx_hash: str
    from_addr: str
    to_addr: str
    amount: float
    data: Dict = field(default_factory=dict)
    timestamp: float = 0.0
    signature: str = ""
    status: str = "pending"

    def to_dict(self) -> Dict:
        return {
            "tx_hash": self.tx_hash,
            "from": self.from_addr,
            "to": self.to_addr,
            "amount": self.amount,
            "data": self.data,
            "timestamp": self.timestamp,
            "signature": self.signature,
            "status": self.status,
        }


@dataclass
class Batch:
    batch_id: str
    txs: List[L2Transaction]
    root_hash: str = ""
    timestamp: float = 0.0
    settled: bool = False


class RollupEngine:
    """Simulates a Solana L2 rollup with aggressive batching.

    In production this would:
    - Run a real sequencer
    - Post state roots to Solana
    - Handle fraud proofs
    Here we simulate the throughput mechanics.
    """

    def __init__(self, config: Dict):
        self.chain_id = config.get("chain_id", 900001)
        self.name = config.get("name", "MacComputeL2")
        self.batch_size = config.get("batch_size", 5000)
        self.batch_interval_ms = config.get("batch_interval_ms", 100)
        self.max_parallel = config.get("max_parallel_batches", 20)
        self.settlement_interval = config.get("settlement_interval_sec", 60)

        self.mempool: deque = deque()
        self.batches: Dict[str, Batch] = {}
        self.state: Dict[str, float] = {"node_reward_pool": 0.0}
        self.block_height = 0
        self.total_processed = 0
        self.running = False
        self._lock = asyncio.Lock()

        # Throughput tracking
        self._tx_times: deque = deque(maxlen=10000)
        self._batch_times: deque = deque(maxlen=1000)

    async def start(self):
        """Start the rollup sequencer."""
        self.running = True
        await asyncio.gather(
            self._batch_producer(),
            self._settlement_loop(),
        )

    async def stop(self):
        self.running = False

    def submit_tx(self, tx: L2Transaction) -> str:
        """Submit a transaction to the L2 mempool."""
        tx.timestamp = time.time()
        tx.tx_hash = self._hash_tx(tx)
        tx.signature = self._sign(tx)
        self.mempool.append(tx)
        return tx.tx_hash

    def submit_compute_receipt(self, node_id: str, task_id: str, reward: float, proof: Dict):
        """Submit a compute task receipt as an L2 transaction."""
        tx = L2Transaction(
            tx_hash="",
            from_addr="compute_market",
            to_addr=node_id,
            amount=reward,
            data={
                "type": "compute_receipt",
                "task_id": task_id,
                "proof": proof,
                "l2_chain": self.name,
            },
        )
        return self.submit_tx(tx)

    async def _batch_producer(self):
        """Continuously form batches from mempool."""
        while self.running:
            batch = await self._form_batch()
            if batch:
                await self._process_batch(batch)
            await asyncio.sleep(self.batch_interval_ms / 1000)

    async def _form_batch(self) -> Optional[Batch]:
        """Grab transactions from mempool and form a batch."""
        if len(self.mempool) < self.batch_size:
            return None

        txs = []
        for _ in range(min(self.batch_size, len(self.mempool))):
            txs.append(self.mempool.popleft())

        batch = Batch(
            batch_id=f"batch-{self.block_height}-{hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]}",
            txs=txs,
            timestamp=time.time(),
        )
        batch.root_hash = self._merkle_root(txs)
        return batch

    async def _process_batch(self, batch: Batch):
        """Process a batch in parallel for speed."""
        start = time.time()

        # Parallel execution across chunks
        chunk_size = max(1, len(batch.txs) // self.max_parallel)
        chunks = [batch.txs[i:i+chunk_size] for i in range(0, len(batch.txs), chunk_size)]

        await asyncio.gather(*[self._execute_chunk(c) for c in chunks])

        batch.settled = True
        self.batches[batch.batch_id] = batch
        self.block_height += 1
        self.total_processed += len(batch.txs)

        elapsed = time.time() - start
        self._batch_times.append(elapsed)
        for tx in batch.txs:
            self._tx_times.append(time.time() - tx.timestamp)

    async def _execute_chunk(self, txs: List[L2Transaction]):
        """Execute a chunk of transactions (simulated)."""
        for tx in txs:
            # Simulate state update
            if tx.to_addr in self.state:
                self.state[tx.to_addr] += tx.amount
            else:
                self.state[tx.to_addr] = tx.amount
            tx.status = "confirmed"
            await asyncio.sleep(0)  # Yield for concurrency

    async def _settlement_loop(self):
        """Periodically settle batches to Solana (simulated)."""
        while self.running:
            await asyncio.sleep(self.settlement_interval)
            pending = [b for b in self.batches.values() if b.settled]
            if pending:
                await self._settle_to_solana(pending)

    async def _settle_to_solana(self, batches: List[Batch]):
        """Post state root to Solana (simulated)."""
        combined_root = hashlib.sha256(
            "".join(b.root_hash for b in batches).encode()
        ).hexdigest()
        print(f"[L2] Settled {len(batches)} batches to Solana. Root: {combined_root[:16]}...")

    def get_tps(self) -> float:
        """Calculate current transactions per second."""
        if not self._batch_times:
            return 0.0
        avg_batch_time = sum(self._batch_times) / len(self._batch_times)
        if avg_batch_time == 0:
            return 0.0
        return round(self.batch_size / avg_batch_time, 2)

    def get_status(self) -> Dict:
        """Return rollup status."""
        tps = self.get_tps()
        avg_latency = 0.0
        if self._tx_times:
            avg_latency = sum(self._tx_times) / len(self._tx_times)

        return {
            "chain_id": self.chain_id,
            "name": self.name,
            "block_height": self.block_height,
            "mempool_size": len(self.mempool),
            "batches_settled": len(self.batches),
            "total_processed": self.total_processed,
            "current_tps": tps,
            "target_tps": 1_000_000,
            "avg_latency_ms": round(avg_latency * 1000, 2),
            "state_root": self._merkle_root([]) if not self.batches else list(self.batches.values())[-1].root_hash[:16] + "...",
        }

    def get_balance(self, address: str) -> float:
        return self.state.get(address, 0.0)

    def _hash_tx(self, tx: L2Transaction) -> str:
        data = f"{tx.from_addr}{tx.to_addr}{tx.amount}{tx.timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()

    def _sign(self, tx: L2Transaction) -> str:
        return hashlib.sha256(f"sig-{tx.tx_hash}".encode()).hexdigest()

    def _merkle_root(self, txs: List[L2Transaction]) -> str:
        if not txs:
            return hashlib.sha256(b"empty").hexdigest()
        hashes = [hashlib.sha256(json.dumps(tx.to_dict()).encode()).digest() for tx in txs]
        while len(hashes) > 1:
            new_level = []
            for i in range(0, len(hashes), 2):
                left = hashes[i]
                right = hashes[i + 1] if i + 1 < len(hashes) else hashes[i]
                new_level.append(hashlib.sha256(left + right).digest())
            hashes = new_level
        return hashes[0].hex()
