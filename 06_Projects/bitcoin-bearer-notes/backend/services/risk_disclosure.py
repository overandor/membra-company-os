"""Risk disclosure acceptance tracking for Membra Money."""
import hashlib
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.config import settings
from models.database import RiskDisclosureAcceptance

CURRENT_DISCLOSURE_VERSION = "1.0.0"

DISCLOSURE_TEXT = """
MEMBRA MONEY RISK DISCLOSURE

1. BTC-backed notes are claims, not native Bitcoin. You do not hold private keys to on-chain BTC.
2. Redemption may require compliance checks, KYC/AML, and reserve availability.
3. Claim links can expire. Loss of claim access may result in loss of claimability.
4. Reserve/custody/federation risk exists. The reserve operator may become insolvent or compromised.
5. SMS and email are insecure transport channels. Claim links may be intercepted.
6. Membra Money does not guarantee profit, yield, redemption timing, or liquidity.
7. Mainnet transactions cost fees and may fail due to network congestion.
8. This is experimental software. Use only funds you can afford to lose.
"""


def get_disclosure_hash() -> str:
    return hashlib.sha256(DISCLOSURE_TEXT.encode()).hexdigest()


class RiskDisclosureService:
    """Manages risk disclosure acceptance for claims and redemptions."""

    @staticmethod
    def current_version() -> str:
        return CURRENT_DISCLOSURE_VERSION

    @staticmethod
    def current_hash() -> str:
        return get_disclosure_hash()

    @staticmethod
    def current_text() -> str:
        return DISCLOSURE_TEXT.strip()

    async def has_accepted(
        self, db: AsyncSession, wallet_address: str, claim_id: Optional[str] = None
    ) -> bool:
        """Check if a wallet has accepted the current disclosure."""
        result = await db.execute(
            select(RiskDisclosureAcceptance)
            .where(RiskDisclosureAcceptance.wallet_address == wallet_address)
            .where(RiskDisclosureAcceptance.disclosure_version == CURRENT_DISCLOSURE_VERSION)
        )
        return result.scalar_one_or_none() is not None

    async def record_acceptance(
        self,
        db: AsyncSession,
        wallet_address: str,
        claim_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> RiskDisclosureAcceptance:
        """Record a new disclosure acceptance."""
        ip_hash = hashlib.sha256(ip_address.encode()).hexdigest() if ip_address else None
        ua_hash = hashlib.sha256(user_agent.encode()).hexdigest() if user_agent else None
        proof = hashlib.sha256(
            f"{wallet_address}:{claim_id or ''}:{CURRENT_DISCLOSURE_VERSION}:{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()

        acceptance = RiskDisclosureAcceptance(
            wallet_address=wallet_address,
            claim_id=claim_id,
            disclosure_version=CURRENT_DISCLOSURE_VERSION,
            disclosure_hash=get_disclosure_hash(),
            ip_hash=ip_hash,
            user_agent_hash=ua_hash,
            proof_hash=proof,
        )
        db.add(acceptance)
        await db.commit()
        await db.refresh(acceptance)
        return acceptance


risk_service = RiskDisclosureService()
