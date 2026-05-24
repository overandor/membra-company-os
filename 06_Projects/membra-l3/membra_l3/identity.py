"""
MEMBRA Identity Layer — Social identity linking and reputation scoring.

Safe version:
- Social metrics are reputation signals, NOT collateral.
- Venmo balance is NOT backing unless funds are escrowed/custodied.
- Users can link social/payment identities.
- Social score affects risk limits (not token supply).
- Claims must be backed by real reserves.
"""
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

from .proof_book import proof_book, ProofType


class IdentityProvider(Enum):
    VENMO = "venmo"
    TWITTER = "twitter"
    GITHUB = "github"
    DISCORD = "discord"
    EMAIL = "email"
    SOLANA_WALLET = "solana_wallet"


class LinkStatus(Enum):
    PENDING = "pending"       # Awaiting verification
    VERIFIED = "verified"     # Proof confirmed
    REVOKED = "revoked"       # Link removed
    FAILED = "failed"         # Verification failed


@dataclass
class IdentityLink:
    link_id: str
    user_address: str          # Solana wallet address
    provider: IdentityProvider
    external_id: str           # e.g., "@venmo_username", "@twitter_handle"
    status: LinkStatus
    verified_at: Optional[float] = None
    proof_data: Dict = field(default_factory=dict)  # verification evidence
    created_at: float = field(default_factory=time.time)


@dataclass
class SocialScore:
    user_address: str
    score: float               # 0.0 - 1.0 reputation score
    linked_providers: int
    account_age_days: float
    activity_signals: int      # number of positive on-chain actions
    risk_flags: List[str]      # any risk indicators
    computed_at: float
    max_transfer_usd: float    # risk-adjusted transfer limit
    max_fee_credits_usd: float # risk-adjusted fee credit cap


class IdentityRegistry:
    """
    Links social/payment identities to Solana addresses.
    Social score affects risk limits, NOT token supply.
    """

    def __init__(self):
        self._links: Dict[str, IdentityLink] = {}  # link_id -> link
        self._user_links: Dict[str, List[str]] = {}  # user_address -> [link_id]
        self._provider_index: Dict[str, Dict[str, str]] = {}  # provider -> external_id -> link_id
        self._scores: Dict[str, SocialScore] = {}

    def link_identity(self, user_address: str, provider: IdentityProvider,
                      external_id: str, proof_data: Optional[Dict] = None) -> IdentityLink:
        """
        Link a social/payment identity to a Solana address.
        Requires verification proof (e.g., signed message, OAuth token).
        """
        # Check if this external_id is already linked
        prov_idx = self._provider_index.setdefault(provider.value, {})
        existing = prov_idx.get(external_id)
        if existing and self._links[existing].status == LinkStatus.VERIFIED:
            # Already linked to another address — flag as risk
            pass

        link = IdentityLink(
            link_id=uuid.uuid4().hex[:16],
            user_address=user_address,
            provider=provider,
            external_id=external_id,
            status=LinkStatus.PENDING,
            proof_data=proof_data or {},
        )

        self._links[link.link_id] = link
        self._user_links.setdefault(user_address, []).append(link.link_id)
        prov_idx[external_id] = link.link_id

        proof_book.append(ProofType.IDENTITY_LINK, {
            "action": "identity_linked",
            "user_address": user_address,
            "provider": provider.value,
            "external_id": external_id,
            "link_id": link.link_id,
        })

        return link

    def verify_link(self, link_id: str, verifier: str = "system") -> bool:
        """Verify a pending identity link."""
        link = self._links.get(link_id)
        if not link or link.status != LinkStatus.PENDING:
            return False

        link.status = LinkStatus.VERIFIED
        link.verified_at = time.time()

        proof_book.append(ProofType.IDENTITY_LINK, {
            "action": "identity_verified",
            "link_id": link_id,
            "verifier": verifier,
        })

        # Recompute social score
        self._compute_score(link.user_address)
        return True

    def revoke_link(self, link_id: str) -> bool:
        link = self._links.get(link_id)
        if not link:
            return False
        link.status = LinkStatus.REVOKED
        self._compute_score(link.user_address)
        return True

    def get_user_links(self, user_address: str) -> List[IdentityLink]:
        link_ids = self._user_links.get(user_address, [])
        return [self._links[lid] for lid in link_ids if lid in self._links]

    def get_verified_providers(self, user_address: str) -> List[IdentityProvider]:
        links = self.get_user_links(user_address)
        return [l.provider for l in links if l.status == LinkStatus.VERIFIED]

    def has_venmo_linked(self, user_address: str) -> bool:
        return IdentityProvider.VENMO in self.get_verified_providers(user_address)

    def get_venmo_username(self, user_address: str) -> Optional[str]:
        for link in self.get_user_links(user_address):
            if link.provider == IdentityProvider.VENMO and link.status == LinkStatus.VERIFIED:
                return link.external_id
        return None

    # ─── Social Scoring ─────────────────────────────────────

    def _compute_score(self, user_address: str) -> SocialScore:
        """Compute reputation score from verified links and activity."""
        links = self.get_user_links(user_address)
        verified = [l for l in links if l.status == LinkStatus.VERIFIED]

        # Base score from linked providers
        provider_weights = {
            IdentityProvider.VENMO: 0.25,
            IdentityProvider.TWITTER: 0.15,
            IdentityProvider.GITHUB: 0.20,
            IdentityProvider.DISCORD: 0.10,
            IdentityProvider.EMAIL: 0.10,
            IdentityProvider.SOLANA_WALLET: 0.20,
        }

        score = 0.0
        for link in verified:
            score += provider_weights.get(link.provider, 0.05)

        score = min(1.0, score)

        # Risk flags
        risk_flags = []
        if len(verified) == 0:
            risk_flags.append("no_verified_identity")
        if len(verified) == 1:
            risk_flags.append("single_identity_only")

        # Check for duplicate external_ids across users
        for link in verified:
            prov_idx = self._provider_index.get(link.provider.value, {})
            if prov_idx.get(link.external_id) != link.link_id:
                risk_flags.append(f"duplicate_{link.provider.value}")

        # Risk-adjusted limits
        max_transfer = 1000.0 * score  # $1000 max for fully verified
        max_fee_credits = 10.0 * score  # $10 max fee credits

        social_score = SocialScore(
            user_address=user_address,
            score=score,
            linked_providers=len(verified),
            account_age_days=0.0,  # would track from first link
            activity_signals=0,
            risk_flags=risk_flags,
            computed_at=time.time(),
            max_transfer_usd=max_transfer,
            max_fee_credits_usd=max_fee_credits,
        )

        self._scores[user_address] = social_score
        return social_score

    def get_score(self, user_address: str) -> Optional[SocialScore]:
        return self._scores.get(user_address)

    def get_risk_adjusted_limits(self, user_address: str) -> tuple:
        """Returns (max_transfer_usd, max_fee_credits_usd)."""
        score = self.get_score(user_address)
        if not score:
            return (100.0, 2.0)  # conservative defaults for unverified
        return (score.max_transfer_usd, score.max_fee_credits_usd)


# Singleton
identity_registry = IdentityRegistry()
