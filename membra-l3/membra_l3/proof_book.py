"""
MEMBRA ProofBook — Immutable append-only proof log.

Records:
- Proof-of-Volatility signals
- Proof-of-Development attestations
- ZK compute receipts
- Governance actions
- Fee credit issuances
- Route validations

Every entry is hashed and chained (prev_hash) for tamper evidence.
"""
import json
import hashlib
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from enum import Enum


class ProofType(Enum):
    VOLATILITY = "proof_of_volatility"
    DEVELOPMENT = "proof_of_development"
    ZK_COMPUTE = "zk_compute_receipt"
    GOVERNANCE = "governance_action"
    FEE_CREDIT = "fee_credit_issuance"
    ROUTE_VALIDATION = "route_validation"
    ORACLE_UPDATE = "oracle_update"
    TREASURY = "treasury_action"
    IDENTITY_LINK = "identity_link"


@dataclass
class ProofEntry:
    proof_type: ProofType
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    prev_hash: str = ""
    entry_hash: str = ""

    def compute_hash(self) -> str:
        payload = json.dumps({
            "type": self.proof_type.value,
            "data": self.data,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def seal(self, prev_hash: str):
        self.prev_hash = prev_hash
        self.entry_hash = self.compute_hash()


class ProofBook:
    """
    Append-only, hash-chained proof log.
    Thread-safe for a single process; use DB backend for multi-process.
    """

    def __init__(self):
        self._entries: List[ProofEntry] = []
        self._last_hash: str = "0" * 64  # genesis hash

    def append(self, proof_type: ProofType, data: Dict[str, Any]) -> ProofEntry:
        entry = ProofEntry(proof_type=proof_type, data=data)
        entry.seal(self._last_hash)
        self._entries.append(entry)
        self._last_hash = entry.entry_hash
        return entry

    def get_entries(self, proof_type: Optional[ProofType] = None,
                    since: Optional[float] = None,
                    limit: int = 100) -> List[ProofEntry]:
        results = self._entries
        if proof_type:
            results = [e for e in results if e.proof_type == proof_type]
        if since:
            results = [e for e in results if e.timestamp >= since]
        return results[-limit:]

    def verify_chain(self) -> bool:
        """Verify the hash chain integrity."""
        expected = "0" * 64
        for entry in self._entries:
            if entry.prev_hash != expected:
                return False
            expected = entry.compute_hash()
            if entry.entry_hash != expected:
                return False
        return True

    @property
    def last_hash(self) -> str:
        return self._last_hash

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    def export(self) -> List[Dict]:
        return [{k: v.value if isinstance(v, Enum) else v for k, v in asdict(e).items()} for e in self._entries]

    def to_json(self) -> str:
        return json.dumps(self.export(), indent=2, default=str)


# Singleton for the L3 process
proof_book = ProofBook()
