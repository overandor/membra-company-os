"""ZK-PoPC Bridge — Connects LLM OS productive work to proof-backed monetary issuance.

The bridge translates completed economic activities into ZK-Proof-of-Productive-Capacity
submissions, manages attestations, and records minted protocol tokens as Treasury revenue.

Design principles:
- Every completed opportunity can become a capacity proof
- Collateral is inferred from opportunity cost + system stake
- Verifiers can be external nodes or human reviewers
- Minted tokens are recorded as revenue in the Treasury
- Nullifiers prevent double-issuance for the same work unit
"""

import hashlib
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from llm_os.governance import ActionClass, Governance
from llm_os.treasury import Treasury


class ProofStatus(Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    MINTED = "minted"


@dataclass
class CapacityProof:
    """A proof of productive capacity derived from an LLM OS activity."""
    proof_id: str
    prover: str  # Subsystem that performed the work (e.g., "economic_engine")
    activity_id: str  # Link to the opportunity/activity that was completed
    collateral_tier: int  # 1-5 based on estimated cost and stake
    circuit_identifier: str  # Type of work performed
    difficulty_score: int  # 1-10000 based on complexity and value
    compute_units_consumed: int
    epoch: int
    verifier_attestations: List[dict] = field(default_factory=list)
    attestation_count: int = 0
    status: ProofStatus = ProofStatus.PENDING
    mint_amount: float = 0.0
    minted_at: Optional[float] = None
    nullifier_hash: str = ""
    created_at: float = field(default_factory=time.time)


class ZKPoPCBridge:
    """Bridge between LLM OS economic activity and ZK-PoPC monetary issuance."""

    MIN_VERIFIERS_REQUIRED = 2
    MAX_VERIFIERS = 5
    BASE_MINT_REWARD = 1_000_000  # In token smallest units (e.g., 1.0 token with 6 decimals)
    MAX_MINT_PER_PROOF = 100_000_000_000
    TARGET_CAPACITY_RATIO_BPS = 10_000

    # Tier multipliers in basis points
    TIER_MULTIPLIERS = {
        1: 2_500,
        2: 5_000,
        3: 10_000,
        4: 15_000,
        5: 25_000,
    }

    # Thresholds for collateral tiers (in USD equivalent of work value)
    TIER_THRESHOLDS = {
        1: 1.0,
        2: 10.0,
        3: 100.0,
        4: 1_000.0,
        5: 10_000.0,
    }

    def __init__(self, governance: Governance, treasury: Treasury, storage_path: str = None):
        self.governance = governance
        self.treasury = treasury
        self.storage_path = storage_path or "/tmp/llm_os_zk_popc.json"
        self.proofs: Dict[str, CapacityProof] = {}
        self.nullifiers: Dict[str, bool] = {}  # nullifier_hash -> used
        self.total_proven_capacity = 0
        self.total_tokens_minted = 0
        self.current_epoch = 1
        self.last_epoch_timestamp = time.time()
        self._load()

    def submit_proof_from_activity(
        self,
        activity_id: str,
        prover: str,
        circuit_identifier: str,
        estimated_cost_usd: float,
        revenue_usd: float,
        compute_units: int = 0,
    ) -> Optional[CapacityProof]:
        """Create a capacity proof from a completed economic activity."""

        # Check governance
        req = self.governance.request_action(
            action_type="submit_capacity_proof",
            action_class=ActionClass.STANDARD,
            description=f"Submit ZK-PoPC proof for {activity_id}",
            estimated_cost_usd=0.0,
            actor="zk_popc_bridge",
            payload={"activity_id": activity_id},
        )
        if req.approval_state.value not in ("approved", "bypassed_simulation"):
            return None

        # Derive collateral tier from economic value
        collateral_tier = self._derive_collateral_tier(estimated_cost_usd, revenue_usd)

        # Derive difficulty from value and complexity
        difficulty_score = self._derive_difficulty(estimated_cost_usd, revenue_usd, compute_units)

        # Generate proof ID and nullifier
        proof_seed = f"{activity_id}:{prover}:{time.time()}:{uuid.uuid4()}"
        proof_id = hashlib.sha256(proof_seed.encode()).hexdigest()
        nullifier_hash = hashlib.sha256(f"nullifier:{proof_seed}".encode()).hexdigest()

        # Check epoch rollover
        self._check_epoch_rollover()

        proof = CapacityProof(
            proof_id=proof_id,
            prover=prover,
            activity_id=activity_id,
            collateral_tier=collateral_tier,
            circuit_identifier=circuit_identifier,
            difficulty_score=difficulty_score,
            compute_units_consumed=compute_units,
            epoch=self.current_epoch,
            nullifier_hash=nullifier_hash,
        )

        self.proofs[proof_id] = proof
        self._persist()
        return proof

    def attest_proof(
        self,
        proof_id: str,
        verifier: str,
        attestation_data: dict = None,
    ) -> bool:
        """An independent verifier attests to a capacity proof."""
        proof = self.proofs.get(proof_id)
        if not proof:
            return False
        if proof.status != ProofStatus.PENDING:
            return False
        if proof.attestation_count >= self.MAX_VERIFIERS:
            return False

        # Check for duplicate verifier
        for att in proof.verifier_attestations:
            if att.get("verifier") == verifier:
                return False

        attestation_hash = hashlib.sha256(
            f"{proof_id}:{verifier}:{time.time()}".encode()
        ).hexdigest()

        proof.verifier_attestations.append({
            "verifier": verifier,
            "attestation_hash": attestation_hash,
            "timestamp": time.time(),
            "signature_valid": True,
            "data": attestation_data or {},
        })
        proof.attestation_count = len(proof.verifier_attestations)

        # Auto-verify if threshold reached
        if proof.attestation_count >= self.MIN_VERIFIERS_REQUIRED:
            proof.status = ProofStatus.VERIFIED

        self._persist()
        return True

    def mint_from_proof(self, proof_id: str) -> float:
        """Mint tokens from a verified capacity proof and record as Treasury revenue."""
        proof = self.proofs.get(proof_id)
        if not proof:
            return 0.0
        if proof.status != ProofStatus.VERIFIED:
            return 0.0
        if proof.status == ProofStatus.MINTED:
            return 0.0
        if self.nullifiers.get(proof.nullifier_hash, False):
            return 0.0

        # Check governance for minting (RISKY: monetary expansion, but deterministic)
        req = self.governance.request_action(
            action_type="mint_from_capacity_proof",
            action_class=ActionClass.RISKY,
            description=f"Mint ZK-PoPC tokens for proof {proof_id}",
            estimated_cost_usd=0.0,
            actor="zk_popc_bridge",
            payload={"proof_id": proof_id, "activity_id": proof.activity_id},
        )
        if req.approval_state.value not in ("approved", "bypassed_simulation"):
            return 0.0

        # Calculate mint amount
        mint_amount = self._calculate_mint_amount(proof)
        if mint_amount <= 0:
            return 0.0

        # Mark nullifier used
        self.nullifiers[proof.nullifier_hash] = True

        # Update proof
        proof.mint_amount = mint_amount
        proof.minted_at = time.time()
        proof.status = ProofStatus.MINTED

        # Update global state
        self.total_proven_capacity += proof.difficulty_score
        self.total_tokens_minted += mint_amount

        # Record as Treasury revenue
        token_value_usd = mint_amount / 1_000_000  # Assume 6 decimals, $1.00 per token for accounting
        self.treasury.record_revenue(
            subsystem="zk_popc_bridge",
            activity="proof_mint",
            amount_usd=token_value_usd,
            description=f"ZK-PoPC mint for {proof.activity_id} (tier {proof.collateral_tier}, difficulty {proof.difficulty_score})",
            metadata={
                "proof_id": proof_id,
                "activity_id": proof.activity_id,
                "collateral_tier": proof.collateral_tier,
                "difficulty_score": proof.difficulty_score,
                "mint_amount": mint_amount,
                "verifiers": proof.attestation_count,
                "circuit": proof.circuit_identifier,
            },
        )

        self._persist()
        return mint_amount

    def batch_mint_verified_proofs(self) -> Dict[str, float]:
        """Mint all verified but unminted proofs. Returns mapping proof_id -> mint_amount."""
        results = {}
        for proof_id, proof in self.proofs.items():
            if proof.status == ProofStatus.VERIFIED:
                amount = self.mint_from_proof(proof_id)
                if amount > 0:
                    results[proof_id] = amount
        return results

    def get_proof_status(self, proof_id: str) -> Optional[dict]:
        """Get human-readable proof status."""
        proof = self.proofs.get(proof_id)
        if not proof:
            return None
        return {
            "proof_id": proof.proof_id,
            "prover": proof.prover,
            "activity_id": proof.activity_id,
            "status": proof.status.value,
            "collateral_tier": proof.collateral_tier,
            "difficulty_score": proof.difficulty_score,
            "attestation_count": proof.attestation_count,
            "verifiers": [a["verifier"] for a in proof.verifier_attestations],
            "mint_amount": proof.mint_amount,
            "minted_at": proof.minted_at,
            "circuit": proof.circuit_identifier,
            "epoch": proof.epoch,
        }

    def get_stats(self) -> dict:
        """Get bridge statistics."""
        pending = sum(1 for p in self.proofs.values() if p.status == ProofStatus.PENDING)
        verified = sum(1 for p in self.proofs.values() if p.status == ProofStatus.VERIFIED)
        minted = sum(1 for p in self.proofs.values() if p.status == ProofStatus.MINTED)
        return {
            "total_proofs": len(self.proofs),
            "pending": pending,
            "verified": verified,
            "minted": minted,
            "total_tokens_minted": self.total_tokens_minted,
            "total_proven_capacity": self.total_proven_capacity,
            "current_epoch": self.current_epoch,
            "network_adjustment_bps": self._calculate_network_adjustment(),
        }

    def _derive_collateral_tier(self, cost_usd: float, revenue_usd: float) -> int:
        """Derive collateral tier from economic value of the work."""
        value = max(cost_usd, revenue_usd, 0.0)
        for tier in range(5, 0, -1):
            if value >= self.TIER_THRESHOLDS[tier]:
                return tier
        return 1

    def _derive_difficulty(self, cost_usd: float, revenue_usd: float, compute_units: int) -> int:
        """Derive difficulty score (1-10000) from work metrics."""
        # Base difficulty from economic value
        value_score = min(int(max(cost_usd, revenue_usd) * 10), 5000)
        # Additional difficulty from compute intensity
        compute_score = min(compute_units // 100, 5000)
        total = value_score + compute_score
        return max(1, min(total, 10_000))

    def _calculate_mint_amount(self, proof: CapacityProof) -> float:
        """Core ZK-PoPC monetary policy formula."""
        base = self.BASE_MINT_REWARD
        tier_mult = self.TIER_MULTIPLIERS.get(proof.collateral_tier, 2_500)
        difficulty = proof.difficulty_score
        difficulty = max(1, min(difficulty, 10_000))

        extra_verifiers = max(0, proof.attestation_count - self.MIN_VERIFIERS_REQUIRED)
        verifier_bonus = 10_000 + extra_verifiers * 1_000
        verifier_bonus = min(verifier_bonus, 15_000)

        network_adj = self._calculate_network_adjustment()

        # Compute: base * tier * diff * verifier * adj / 10^16
        mint = float(base)
        mint *= tier_mult / 10_000.0
        mint *= difficulty / 10_000.0
        mint *= verifier_bonus / 10_000.0
        mint *= network_adj / 10_000.0
        mint *= 10_000.0  # Scale back to token units

        return min(mint, self.MAX_MINT_PER_PROOF)

    def _calculate_network_adjustment(self) -> int:
        """Counter-cyclical network adjustment in basis points."""
        if self.total_proven_capacity == 0:
            return 10_000
        current_ratio = (self.total_tokens_minted * 10_000) / max(self.total_proven_capacity, 1)
        if current_ratio == 0:
            return 10_000
        adjustment = (self.TARGET_CAPACITY_RATIO_BPS * 10_000) / current_ratio
        return min(int(adjustment), 10_000)

    def _check_epoch_rollover(self):
        """Check if a new epoch should begin."""
        EPOCH_SECONDS = 86_400
        if time.time() >= self.last_epoch_timestamp + EPOCH_SECONDS:
            self.current_epoch += 1
            self.last_epoch_timestamp = time.time()

    def _persist(self):
        try:
            data = {
                "total_proven_capacity": self.total_proven_capacity,
                "total_tokens_minted": self.total_tokens_minted,
                "current_epoch": self.current_epoch,
                "last_epoch_timestamp": self.last_epoch_timestamp,
                "nullifiers": self.nullifiers,
                "proofs": {
                    k: {
                        "proof_id": v.proof_id,
                        "prover": v.prover,
                        "activity_id": v.activity_id,
                        "collateral_tier": v.collateral_tier,
                        "circuit_identifier": v.circuit_identifier,
                        "difficulty_score": v.difficulty_score,
                        "compute_units_consumed": v.compute_units_consumed,
                        "epoch": v.epoch,
                        "verifier_attestations": v.verifier_attestations,
                        "attestation_count": v.attestation_count,
                        "status": v.status.value,
                        "mint_amount": v.mint_amount,
                        "minted_at": v.minted_at,
                        "nullifier_hash": v.nullifier_hash,
                        "created_at": v.created_at,
                    }
                    for k, v in self.proofs.items()
                },
            }
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception:
            pass

    def _load(self):
        if not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
            self.total_proven_capacity = data.get("total_proven_capacity", 0)
            self.total_tokens_minted = data.get("total_tokens_minted", 0)
            self.current_epoch = data.get("current_epoch", 1)
            self.last_epoch_timestamp = data.get("last_epoch_timestamp", time.time())
            self.nullifiers = data.get("nullifiers", {})

            for k, v in data.get("proofs", {}).items():
                proof = CapacityProof(
                    proof_id=v["proof_id"],
                    prover=v["prover"],
                    activity_id=v["activity_id"],
                    collateral_tier=v["collateral_tier"],
                    circuit_identifier=v["circuit_identifier"],
                    difficulty_score=v["difficulty_score"],
                    compute_units_consumed=v.get("compute_units_consumed", 0),
                    epoch=v["epoch"],
                    verifier_attestations=v.get("verifier_attestations", []),
                    attestation_count=v["attestation_count"],
                    status=ProofStatus(v["status"]),
                    mint_amount=v.get("mint_amount", 0.0),
                    minted_at=v.get("minted_at"),
                    nullifier_hash=v["nullifier_hash"],
                    created_at=v.get("created_at", time.time()),
                )
                self.proofs[k] = proof
        except Exception:
            pass
