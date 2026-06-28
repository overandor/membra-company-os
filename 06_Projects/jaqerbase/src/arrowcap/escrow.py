"""Escrow: the state machine that enforces ArrowCAP's first law.

    No full disclosure before payment.
    No payment without settlement.
    No settlement without an oracle.
    No oracle without a bond.

This becomes a strict ordering on every AnswerClaim:

    preview -> bonded -> funded -> revealed -> settled

Each transition below refuses to run unless the AnswerClaim is in the exact
prior state, so the ordering is a code-level invariant (ProtocolViolation)
rather than a convention callers have to remember.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from .antonymizer import AntonymProfile, verify_binding
from .claims import AnswerClaim, Claim, ClaimStore
from .ledger import Ledger
from .oracle import OracleReport, run_hidden_tests


class ProtocolViolation(Exception):
    """Raised when a transition is attempted out of the first-law order."""


@dataclass
class SettlementOutcome:
    answer_id: str
    claim_id: str
    buyer_account: str
    seller_account: str
    treasury_account: str
    passed: bool
    binding_violation: bool
    reward_cents: int
    fee_cents: int
    payout_cents: int
    bond_cents: int
    bond_returned: bool
    oracle_report: Optional[dict]
    resolved_at: float

    def to_dict(self) -> dict:
        return {
            "answer_id": self.answer_id,
            "claim_id": self.claim_id,
            "buyer_account": self.buyer_account,
            "seller_account": self.seller_account,
            "treasury_account": self.treasury_account,
            "passed": self.passed,
            "binding_violation": self.binding_violation,
            "reward_cents": self.reward_cents,
            "fee_cents": self.fee_cents,
            "payout_cents": self.payout_cents,
            "bond_cents": self.bond_cents,
            "bond_returned": self.bond_returned,
            "oracle_report": self.oracle_report,
            "resolved_at": self.resolved_at,
        }


class EscrowEngine:
    def __init__(
        self, ledger: Ledger, store: ClaimStore, *,
        treasury_account: str = "treasury", fee_bps: int = 250,
    ):
        self.ledger = ledger
        self.store = store
        self.treasury_account = treasury_account
        self.fee_bps = fee_bps
        self.ledger.open_account(treasury_account)

    def post_claim(
        self, buyer_account: str, title: str, description: str, reward_cents: int,
        hidden_test_path: str,
    ) -> Claim:
        self.ledger.open_account(buyer_account)
        return self.store.create_claim(
            buyer_account, title, description, reward_cents, hidden_test_path
        )

    def submit_preview(
        self, claim_id: str, seller_account: str, antonym_profile: AntonymProfile,
        bond_cents: int,
    ) -> AnswerClaim:
        self.ledger.open_account(seller_account)
        claim = self.store.get_claim(claim_id)
        if claim.status != "open":
            raise ProtocolViolation(
                f"claim {claim_id} is not open for new previews (status={claim.status})"
            )
        return self.store.submit_preview(claim_id, seller_account, antonym_profile, bond_cents)

    def post_bond(self, answer_id: str) -> int:
        answer = self.store.get_answer(answer_id)
        if answer.status != "preview":
            raise ProtocolViolation(
                f"answer {answer_id} must be 'preview' to post a bond (status={answer.status})"
            )
        hold_id = self.ledger.create_hold(answer.seller_account, answer.bond_cents, "bond", answer_id)
        self.store.set_bond_hold(answer_id, hold_id)
        return hold_id

    def fund_escrow(self, answer_id: str) -> int:
        answer = self.store.get_answer(answer_id)
        if answer.status != "bonded":
            raise ProtocolViolation(
                f"answer {answer_id} must be 'bonded' before escrow can be funded "
                f"(status={answer.status}); no oracle without a bond"
            )
        claim = self.store.get_claim(answer.claim_id)
        hold_id = self.ledger.create_hold(claim.buyer_account, claim.reward_cents, "escrow", answer_id)
        self.store.set_escrow_hold(answer_id, hold_id)
        self.store.set_claim_status(claim.claim_id, "escrowed")
        return hold_id

    def reveal_answer(self, answer_id: str, content: bytes) -> tuple[bool, list[str]]:
        answer = self.store.get_answer(answer_id)
        if answer.status != "funded":
            raise ProtocolViolation(
                f"answer {answer_id} must be 'funded' before disclosure "
                f"(status={answer.status}); no full disclosure before payment"
            )
        ok, mismatches = verify_binding(answer.antonym_profile, content)
        self.store.set_revealed_answer(answer_id, content)
        return ok, mismatches

    def run_oracle(
        self, answer_id: str, *, answer_module_name: str = "submitted_answer",
        timeout_seconds: int = 30,
    ) -> OracleReport:
        answer = self.store.get_answer(answer_id)
        if answer.status != "revealed":
            raise ProtocolViolation(
                f"answer {answer_id} must be 'revealed' before the oracle can run "
                f"(status={answer.status})"
            )
        if answer.revealed_answer is None:
            raise ProtocolViolation(f"answer {answer_id} has no revealed content to test")
        claim = self.store.get_claim(answer.claim_id)
        report = run_hidden_tests(
            answer.revealed_answer, claim.hidden_test_path,
            answer_module_name=answer_module_name, timeout_seconds=timeout_seconds,
        )
        self.store.set_oracle_result(answer_id, report.passed, report.to_dict())
        return report

    def settle(self, answer_id: str, *, binding_violation: bool = False) -> SettlementOutcome:
        answer = self.store.get_answer(answer_id)
        if answer.oracle_passed is None and not binding_violation:
            raise ProtocolViolation(
                f"answer {answer_id} has no oracle result; no settlement without an oracle"
            )
        if answer.bond_hold_id is None or answer.escrow_hold_id is None:
            raise ProtocolViolation(f"answer {answer_id} is missing bond/escrow holds")

        claim = self.store.get_claim(answer.claim_id)
        passed = bool(answer.oracle_passed) and not binding_violation

        if passed:
            fee_cents = (claim.reward_cents * self.fee_bps) // 10000
            payout_cents = claim.reward_cents - fee_cents
            self.ledger.release_hold(answer.escrow_hold_id, destination_account_id=answer.seller_account)
            if fee_cents > 0:
                self.ledger.transfer(
                    answer.seller_account, self.treasury_account, fee_cents,
                    ref_id=answer_id, memo="protocol fee",
                )
            self.ledger.release_hold(answer.bond_hold_id)  # bond returned to seller
            bond_returned = True
        else:
            fee_cents = 0
            payout_cents = 0
            self.ledger.release_hold(answer.escrow_hold_id)  # refund to buyer
            self.ledger.slash_hold(answer.bond_hold_id, claim.buyer_account)  # compensate buyer
            bond_returned = False

        self.store.set_settled(answer_id)
        self.store.set_claim_status(claim.claim_id, "resolved")

        return SettlementOutcome(
            answer_id=answer_id,
            claim_id=claim.claim_id,
            buyer_account=claim.buyer_account,
            seller_account=answer.seller_account,
            treasury_account=self.treasury_account,
            passed=passed,
            binding_violation=binding_violation,
            reward_cents=claim.reward_cents,
            fee_cents=fee_cents,
            payout_cents=payout_cents,
            bond_cents=answer.bond_cents,
            bond_returned=bond_returned,
            oracle_report=answer.oracle_report,
            resolved_at=time.time(),
        )
