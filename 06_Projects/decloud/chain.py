"""Chain — Append-only deployment registry with content-addressed blocks.

Each block links to the previous via SHA-256 hash, creating a tamper-evident
log of all deployments, updates, and deletions across the network.
"""
import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional
import asyncio


@dataclass
class DeploymentRecord:
    """A single deployment action on the chain."""
    app_id: str                          # human-readable app name / subdomain
    cid: str                             # content hash of the app bundle
    owner: str                           # public key or wallet address
    action: str                          # "deploy", "update", "delete", "rollback"
    timestamp: float = field(default_factory=time.time)
    prev_cid: Optional[str] = None       # for rollback: CID to revert to
    metadata: dict = field(default_factory=dict)

    def canonical(self) -> str:
        """Deterministic string for hashing."""
        return json.dumps({
            "app_id": self.app_id,
            "cid": self.cid,
            "owner": self.owner,
            "action": self.action,
            "timestamp": self.timestamp,
            "prev_cid": self.prev_cid,
            "metadata": self.metadata,
        }, sort_keys=True, separators=(",", ":"))


@dataclass
class Block:
    """One link in the deployment chain."""
    index: int
    timestamp: float
    records: List[DeploymentRecord]
    prev_hash: str
    nonce: int = 0
    hash: str = field(default="")

    def compute_hash(self) -> str:
        payload = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "records": [json.loads(r.canonical()) for r in self.records],
            "prev_hash": self.prev_hash,
            "nonce": self.nonce,
        }, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()

    def seal(self) -> "Block":
        self.hash = self.compute_hash()
        return self


class DeploymentChain:
    """Append-only chain of deployment blocks, persisted to disk."""

    def __init__(self, data_dir: str = "./decloud_chain"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.chain_file = self.data_dir / "chain.jsonl"
        self.blocks: List[Block] = []
        self._index: Dict[str, DeploymentRecord] = {}  # app_id -> latest record
        self._lock = asyncio.Lock()
        self._load()
        if not self.blocks:
            self._genesis()

    def _genesis(self):
        genesis = Block(
            index=0,
            timestamp=time.time(),
            records=[],
            prev_hash="0" * 64,
        ).seal()
        self.blocks.append(genesis)
        self._append_file(genesis)

    def _load(self):
        if not self.chain_file.exists():
            return
        with self.chain_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    raw = json.loads(line)
                    records = [DeploymentRecord(**r) for r in raw.get("records", [])]
                    block = Block(
                        index=raw["index"],
                        timestamp=raw["timestamp"],
                        records=records,
                        prev_hash=raw["prev_hash"],
                        nonce=raw.get("nonce", 0),
                        hash=raw["hash"],
                    )
                    self.blocks.append(block)
                    for rec in records:
                        self._index[rec.app_id] = rec
                except Exception:
                    continue

    def _append_file(self, block: Block):
        with self.chain_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "index": block.index,
                "timestamp": block.timestamp,
                "records": [json.loads(r.canonical()) for r in block.records],
                "prev_hash": block.prev_hash,
                "nonce": block.nonce,
                "hash": block.hash,
            }, sort_keys=True, separators=(",", ":")) + "\n")

    async def add_records(self, records: List[DeploymentRecord]) -> Block:
        async with self._lock:
            prev = self.blocks[-1]
            block = Block(
                index=prev.index + 1,
                timestamp=time.time(),
                records=records,
                prev_hash=prev.hash,
            ).seal()
            self.blocks.append(block)
            self._append_file(block)
            for rec in records:
                self._index[rec.app_id] = rec
            return block

    def get_latest(self, app_id: str) -> Optional[DeploymentRecord]:
        return self._index.get(app_id)

    def get_history(self, app_id: str) -> List[DeploymentRecord]:
        return [r for b in self.blocks for r in b.records if r.app_id == app_id]

    def list_apps(self) -> List[str]:
        return list(self._index.keys())

    def validate(self) -> bool:
        """Quick integrity check: hashes and linkage."""
        for i, block in enumerate(self.blocks):
            if block.hash != block.compute_hash():
                return False
            if i > 0 and block.prev_hash != self.blocks[i - 1].hash:
                return False
        return True

    def get_tip(self) -> Block:
        return self.blocks[-1]
