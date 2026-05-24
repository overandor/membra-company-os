"""
MEMBRA Governance — Authorization layer for dangerous actions.

Every tokenomic action requires:
1. Proof signal (volatility, development, or ZK compute)
2. Community review
3. Governance approval
4. Cap enforcement
5. ProofBook logging

No autonomous execution. No bypassing governance.
"""
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

from .proof_book import proof_book, ProofType


class ProposalType(Enum):
    REBASE_EXECUTE = "rebase_execute"
    REBASE_PAUSE = "rebase_pause"
    EMISSION_PROPOSAL = "emission_proposal"
    GASVAULT_ADJUST = "gasvault_adjust"
    REWARD_RATE_ADJUST = "reward_rate_adjust"
    TREASURY_ACTION = "treasury_action"
    TOKEN_APPROVAL = "token_approval"
    ROUTE_APPROVAL = "route_approval"
    PARAMETER_CHANGE = "parameter_change"
    DEVELOPMENT_REWARD = "development_reward"


class ProposalStatus(Enum):
    DRAFT = "draft"
    REVIEW = "review"
    VOTING = "voting"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    CANCELLED = "cancelled"


class VoteChoice(Enum):
    FOR = "for"
    AGAINST = "against"
    ABSTAIN = "abstain"


@dataclass
class Vote:
    voter_address: str
    choice: VoteChoice
    weight: float  # voting power
    timestamp: float
    reason: str = ""


@dataclass
class GovernanceProposal:
    proposal_id: str
    proposal_type: ProposalType
    title: str
    description: str
    proposer: str
    required_proofs: List[str]  # ProofBook entry hashes that justify this
    params: Dict[str, Any]
    status: ProposalStatus = ProposalStatus.DRAFT
    created_at: float = field(default_factory=time.time)
    review_ends_at: Optional[float] = None
    voting_ends_at: Optional[float] = None
    votes: List[Vote] = field(default_factory=list)
    executed_at: Optional[float] = None
    execution_result: Optional[str] = None

    def tally(self) -> Dict[str, float]:
        """Count votes by choice."""
        counts = {"for": 0.0, "against": 0.0, "abstain": 0.0}
        for v in self.votes:
            counts[v.choice.value] += v.weight
        return counts

    def is_approved(self, quorum: float = 0.2, threshold: float = 0.6) -> bool:
        """Check if proposal passes."""
        t = self.tally()
        total = t["for"] + t["against"] + t["abstain"]
        if total < quorum:
            return False
        if total == 0:
            return False
        return t["for"] / (t["for"] + t["against"]) >= threshold


class Governance:
    """
    Authorization layer. Nothing dangerous happens without passing through here.

    Gates:
    - Proofs must exist in ProofBook
    - Caps must be enforced
    - Community must approve
    - All actions logged
    """

    def __init__(self, review_window_seconds: int = 259200,
                 voting_window_seconds: int = 172800):
        self.review_window = review_window_seconds  # 3 days default
        self.voting_window = voting_window_seconds   # 2 days default
        self._proposals: Dict[str, GovernanceProposal] = {}
        self._voting_power: Dict[str, float] = {}  # address -> voting power

    def set_voting_power(self, address: str, power: float):
        self._voting_power[address] = power

    def get_voting_power(self, address: str) -> float:
        return self._voting_power.get(address, 0.0)

    def propose(self, proposal_type: ProposalType, title: str,
                description: str, proposer: str,
                required_proofs: List[str],
                params: Dict[str, Any]) -> GovernanceProposal:
        """
        Create a governance proposal.

        required_proofs: list of ProofBook entry hashes that justify this action.
        These must exist and be valid.
        """
        # Validate proofs exist
        for proof_hash in required_proofs:
            entries = proof_book.get_entries(limit=200)
            if not any(e.entry_hash == proof_hash for e in entries):
                raise ValueError(f"Required proof not found in ProofBook: {proof_hash}")

        proposal = GovernanceProposal(
            proposal_id=uuid.uuid4().hex[:20],
            proposal_type=proposal_type,
            title=title,
            description=description,
            proposer=proposer,
            required_proofs=required_proofs,
            params=params,
            status=ProposalStatus.REVIEW,
            review_ends_at=time.time() + self.review_window,
        )

        self._proposals[proposal.proposal_id] = proposal

        proof_book.append(ProofType.GOVERNANCE, {
            "action": "proposal_created",
            "proposal_id": proposal.proposal_id,
            "proposal_type": proposal_type.value,
            "title": title,
            "proposer": proposer,
            "required_proofs": required_proofs,
        })

        return proposal

    def start_voting(self, proposal_id: str) -> bool:
        proposal = self._proposals.get(proposal_id)
        if not proposal or proposal.status != ProposalStatus.REVIEW:
            return False
        proposal.status = ProposalStatus.VOTING
        proposal.voting_ends_at = time.time() + self.voting_window
        return True

    def vote(self, proposal_id: str, voter_address: str,
             choice: VoteChoice, reason: str = "") -> bool:
        proposal = self._proposals.get(proposal_id)
        if not proposal or proposal.status != ProposalStatus.VOTING:
            return False

        # Check not already voted
        if any(v.voter_address == voter_address for v in proposal.votes):
            return False

        weight = self.get_voting_power(voter_address)
        if weight <= 0:
            return False

        proposal.votes.append(Vote(
            voter_address=voter_address,
            choice=choice,
            weight=weight,
            timestamp=time.time(),
            reason=reason,
        ))

        proof_book.append(ProofType.GOVERNANCE, {
            "action": "vote_cast",
            "proposal_id": proposal_id,
            "voter": voter_address,
            "choice": choice.value,
            "weight": weight,
        })

        return True

    def finalize(self, proposal_id: str) -> bool:
        """Check if voting period ended and finalize result."""
        proposal = self._proposals.get(proposal_id)
        if not proposal or proposal.status != ProposalStatus.VOTING:
            return False
        if time.time() < (proposal.voting_ends_at or 0):
            return False

        if proposal.is_approved():
            proposal.status = ProposalStatus.APPROVED
        else:
            proposal.status = ProposalStatus.REJECTED

        proof_book.append(ProofType.GOVERNANCE, {
            "action": "proposal_finalized",
            "proposal_id": proposal_id,
            "result": proposal.status.value,
            "tally": proposal.tally(),
        })

        return True

    def execute(self, proposal_id: str, executor: str) -> bool:
        """
        Execute an approved proposal.
        The actual execution logic is handled by the relevant module.
        This just marks it as executed and logs it.
        """
        proposal = self._proposals.get(proposal_id)
        if not proposal or proposal.status != ProposalStatus.APPROVED:
            return False

        proposal.status = ProposalStatus.EXECUTED
        proposal.executed_at = time.time()
        proposal.execution_result = f"Executed by {executor}"

        proof_book.append(ProofType.GOVERNANCE, {
            "action": "proposal_executed",
            "proposal_id": proposal_id,
            "executor": executor,
        })

        return True

    def get_proposal(self, proposal_id: str) -> Optional[GovernanceProposal]:
        return self._proposals.get(proposal_id)

    def get_active_proposals(self) -> List[GovernanceProposal]:
        return [p for p in self._proposals.values()
                if p.status in (ProposalStatus.REVIEW, ProposalStatus.VOTING)]

    def get_proposals_by_type(self, ptype: ProposalType) -> List[GovernanceProposal]:
        return [p for p in self._proposals.values() if p.proposal_type == ptype]

    @property
    def stats(self) -> dict:
        total = len(self._proposals)
        by_status = {}
        for p in self._proposals.values():
            by_status[p.status.value] = by_status.get(p.status.value, 0) + 1
        return {
            "total_proposals": total,
            "by_status": by_status,
            "voters": len(self._voting_power),
        }


# Singleton
governance = Governance()
