"""
MEMBRA GasVault — Fee credit accounting and relayer reimbursement.

Rules:
- Computation does NOT create lamports.
- Users earn fee credits from verified ZK compute, not free SOL.
- Relayers pay real Solana gas fees.
- GasVault reimburses relayers from real SOL reserves.
- Coverage ratio must stay above minimum.
"""
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

from .config import L3Config, DEFAULT_CONFIG
from .proof_book import proof_book, ProofType


class CreditStatus(Enum):
    ACTIVE = "active"
    USED = "used"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass
class FeeCredit:
    credit_id: str
    user_address: str
    amount_lamports: int
    issued_at: float
    expires_at: float
    proof_ref: str  # hash of the ZK proof that earned this credit
    status: CreditStatus = CreditStatus.ACTIVE


@dataclass
class Reimbursement:
    reimbursement_id: str
    relayer_address: str
    amount_lamports: int
    tx_signature: str
    credit_ids: List[str]  # which credits were consumed
    reimbursed_at: float
    coverage_ratio_after: float


class GasVault:
    """
    Manages fee credits and relayer reimbursements.

    Invariants:
    - total_credits_outstanding + sol_reserves >= total_credits_outstanding * coverage_ratio
    - No credit issued without a valid ZK proof in ProofBook
    - No reimbursement without consumed credits
    """

    def __init__(self, config: L3Config = DEFAULT_CONFIG, initial_sol_lamports: int = 0):
        self.config = config
        self.sol_reserves: int = initial_sol_lamports  # real SOL in the vault
        self._credits: Dict[str, FeeCredit] = {}
        self._reimbursements: List[Reimbursement] = []
        self._user_credits: Dict[str, List[str]] = {}  # user_address -> [credit_id]

    # ─── Reserves ───────────────────────────────────────────

    def deposit_sol(self, amount_lamports: int, source: str = "treasury"):
        """Deposit real SOL into the vault."""
        self.sol_reserves += amount_lamports
        proof_book.append(ProofType.TREASURY, {
            "action": "gas_vault_deposit",
            "amount_lamports": amount_lamports,
            "source": source,
            "new_reserves": self.sol_reserves,
        })

    def withdraw_sol(self, amount_lamports: int, destination: str, reason: str) -> bool:
        """Withdraw SOL (governance-gated in production)."""
        if amount_lamports > self.sol_reserves:
            return False
        new_coverage = self._compute_coverage_ratio_after(-amount_lamports)
        if new_coverage < self.config.gas_vault_min_coverage_ratio:
            return False
        self.sol_reserves -= amount_lamports
        proof_book.append(ProofType.TREASURY, {
            "action": "gas_vault_withdraw",
            "amount_lamports": amount_lamports,
            "destination": destination,
            "reason": reason,
            "new_reserves": self.sol_reserves,
        })
        return True

    # ─── Fee Credits ────────────────────────────────────────

    def issue_credit(self, user_address: str, zk_proof_hash: str,
                     work_score: float) -> Optional[FeeCredit]:
        """
        Issue fee credits based on verified ZK compute.
        work_score determines how many lamports of credit (capped).
        """
        # Verify the ZK proof exists in ProofBook
        proofs = proof_book.get_entries(ProofType.ZK_COMPUTE, limit=50)
        matching = [p for p in proofs if p.entry_hash == zk_proof_hash]
        if not matching:
            return None

        # Check user cap
        user_total = self._user_outstanding_lamports(user_address)
        max_lamports = int(self.config.max_fee_credit_per_user_usd * 1e9)  # ~$10 in lamports
        if user_total >= max_lamports:
            return None

        # Compute credit amount (capped)
        credit_lamports = min(
            int(work_score * 1e8),  # 0.1 SOL per work score point
            max_lamports - user_total,
        )
        if credit_lamports <= 0:
            return None

        # Check coverage
        if not self._can_cover_new_credits(credit_lamports):
            return None

        credit = FeeCredit(
            credit_id=uuid.uuid4().hex[:16],
            user_address=user_address,
            amount_lamports=credit_lamports,
            issued_at=time.time(),
            expires_at=time.time() + self.config.fee_credit_expiry_seconds,
            proof_ref=zk_proof_hash,
        )

        self._credits[credit.credit_id] = credit
        self._user_credits.setdefault(user_address, []).append(credit.credit_id)

        proof_book.append(ProofType.FEE_CREDIT, {
            "credit_id": credit.credit_id,
            "user_address": user_address,
            "amount_lamports": credit_lamports,
            "proof_ref": zk_proof_hash,
            "expires_at": credit.expires_at,
        })

        return credit

    def get_user_credits(self, user_address: str) -> List[FeeCredit]:
        self._expire_stale_credits()
        credit_ids = self._user_credits.get(user_address, [])
        return [self._credits[cid] for cid in credit_ids
                if cid in self._credits and self._credits[cid].status == CreditStatus.ACTIVE]

    def consume_credits(self, credit_ids: List[str]) -> int:
        """Mark credits as used, return total lamports consumed."""
        total = 0
        for cid in credit_ids:
            credit = self._credits.get(cid)
            if credit and credit.status == CreditStatus.ACTIVE:
                credit.status = CreditStatus.USED
                total += credit.amount_lamports
        return total

    # ─── Relayer Reimbursement ──────────────────────────────

    def reimburse_relayer(self, relayer_address: str, tx_signature: str,
                          credit_ids: List[str]) -> Optional[Reimbursement]:
        """
        Reimburse a relayer for gas they paid.
        Requires: credits were consumed, vault has SOL, coverage stays healthy.
        """
        total_lamports = self.consume_credits(credit_ids)
        if total_lamports <= 0:
            return None

        if total_lamports > self.sol_reserves:
            # Can't reimburse more than we have
            return None

        new_coverage = self._compute_coverage_ratio_after(-total_lamports)
        if new_coverage < self.config.gas_vault_min_coverage_ratio:
            return None

        self.sol_reserves -= total_lamports

        reimbursement = Reimbursement(
            reimbursement_id=uuid.uuid4().hex[:16],
            relayer_address=relayer_address,
            amount_lamports=total_lamports,
            tx_signature=tx_signature,
            credit_ids=credit_ids,
            reimbursed_at=time.time(),
            coverage_ratio_after=new_coverage,
        )
        self._reimbursements.append(reimbursement)

        proof_book.append(ProofType.TREASURY, {
            "action": "relayer_reimbursement",
            "relayer": relayer_address,
            "amount_lamports": total_lamports,
            "tx_signature": tx_signature,
            "coverage_ratio_after": new_coverage,
        })

        return reimbursement

    # ─── Coverage ───────────────────────────────────────────

    @property
    def coverage_ratio(self) -> float:
        outstanding = self._total_outstanding_lamports()
        if outstanding == 0:
            return float('inf')
        return self.sol_reserves / outstanding

    def is_healthy(self) -> bool:
        return self.coverage_ratio >= self.config.gas_vault_min_coverage_ratio

    def needs_refill(self) -> bool:
        return self.coverage_ratio < self.config.gas_vault_target_coverage_ratio

    # ─── Internal ───────────────────────────────────────────

    def _total_outstanding_lamports(self) -> int:
        self._expire_stale_credits()
        return sum(c.amount_lamports for c in self._credits.values()
                   if c.status == CreditStatus.ACTIVE)

    def _user_outstanding_lamports(self, user_address: str) -> int:
        self._expire_stale_credits()
        credit_ids = self._user_credits.get(user_address, [])
        return sum(self._credits[cid].amount_lamports for cid in credit_ids
                   if cid in self._credits and self._credits[cid].status == CreditStatus.ACTIVE)

    def _can_cover_new_credits(self, additional_lamports: int) -> bool:
        new_outstanding = self._total_outstanding_lamports() + additional_lamports
        if new_outstanding == 0:
            return True
        return self.sol_reserves / new_outstanding >= self.config.gas_vault_min_coverage_ratio

    def _compute_coverage_ratio_after(self, sol_delta: int) -> float:
        new_sol = self.sol_reserves + sol_delta
        outstanding = self._total_outstanding_lamports()
        if outstanding == 0:
            return float('inf')
        return new_sol / outstanding

    def _expire_stale_credits(self):
        now = time.time()
        for credit in self._credits.values():
            if credit.status == CreditStatus.ACTIVE and now >= credit.expires_at:
                credit.status = CreditStatus.EXPIRED

    @property
    def stats(self) -> dict:
        return {
            "sol_reserves": self.sol_reserves,
            "sol_reserves_sol": self.sol_reserves / 1e9,
            "outstanding_credits_lamports": self._total_outstanding_lamports(),
            "coverage_ratio": round(self.coverage_ratio, 4),
            "is_healthy": self.is_healthy(),
            "needs_refill": self.needs_refill(),
            "active_credits": sum(1 for c in self._credits.values() if c.status == CreditStatus.ACTIVE),
            "total_reimbursements": len(self._reimbursements),
        }


# Singleton
gas_vault = GasVault()
