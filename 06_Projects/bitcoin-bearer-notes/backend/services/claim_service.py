"""CoinPack claim link management with anti-double-claim."""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_

from core.config import settings
from models.database import ClaimBundle, ClaimAttempt, AuditLog, NoteRecord


class ClaimService:
    """Manages CoinPack claim links with PIN, expiration, and anti-double-claim."""

    @staticmethod
    def _hash_pin(pin: str, salt: str) -> str:
        """HMAC-based PIN hash with per-claim salt and global pepper."""
        peppered = f"{pin}:{salt}:{settings.PIN_PEPPER}"
        return hashlib.sha256(peppered.encode()).hexdigest()

    @staticmethod
    def _hash_pin_legacy(pin: str) -> str:
        """Legacy unsalted SHA-256 for migration compatibility only.
        DO NOT use for new claims. This exists to verify old claims
        created before the salt+pepper hardening.
        """
        return hashlib.sha256(pin.encode()).hexdigest()

    @staticmethod
    def _mask_claim_url(url: str) -> str:
        """Mask a claim URL for safe logging (replaces claim ID with ***)."""
        if not url:
            return url
        try:
            # Replace anything that looks like a claim ID hex string
            import re
            return re.sub(r"/claim/[a-f0-9]{32,64}", "/claim/**REDacted**", url, flags=re.IGNORECASE)
        except Exception:
            return url

    @staticmethod
    def _generate_salt() -> str:
        return secrets.token_hex(16)

    @staticmethod
    def _generate_claim_hash(claim_id: str) -> str:
        """HMAC integrity check for claim_id tampering."""
        return hmac.new(
            settings.CLAIM_LINK_SECRET.encode(),
            claim_id.encode(),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def generate_claim_id() -> str:
        """Generate a cryptographically secure claim ID."""
        return secrets.token_hex(32)

    @staticmethod
    def generate_pin(length: int = 6) -> str:
        """Generate a random numeric PIN."""
        return ''.join(str(secrets.randbelow(10)) for _ in range(length))

    async def create_claim(
        self,
        db: AsyncSession,
        creator: str,
        assets: List[Dict[str, float]],
        pin: str,
        expires_hours: int,
        delivery_method: str = "link",
        delivery_address: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict:
        """Create a new CoinPack claim bundle."""
        claim_id = self.generate_claim_id()
        salt = self._generate_salt()
        pin_hash = self._hash_pin(pin, salt)
        claim_hash = self._generate_claim_hash(claim_id)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)

        asset_types = [a["type"] for a in assets]
        amounts = [a["amount"] for a in assets]

        claim = ClaimBundle(
            claim_id=claim_id,
            claim_hash=claim_hash,
            creator=creator,
            asset_types=asset_types,
            amounts=amounts,
            expires_at=expires_at,
            pin_hash=pin_hash,
            pin_salt=salt,
            claimed=False,
            delivery_method=delivery_method,
            delivery_address=delivery_address,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        db.add(claim)
        await db.commit()
        await db.refresh(claim)

        # Audit log
        audit = AuditLog(
            event_type="claim_created",
            wallet_address=creator,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "claim_id": claim_id,
                "asset_count": len(assets),
                "expires_at": expires_at.isoformat(),
            },
        )
        db.add(audit)
        await db.commit()

        return {
            "claim_id": claim_id,
            "claim_url": f"{settings.FRONTEND_BASE_URL}/claim/{claim_id}",
            "pin": pin,  # Shown once at creation; caller must display securely and not log
            "expires_at": expires_at.isoformat(),
            "assets": assets,
            "security_notice": "PIN is shown once. Store it securely. It cannot be retrieved later.",
        }

    async def get_claim(self, db: AsyncSession, claim_id: str) -> Optional[ClaimBundle]:
        """Get a claim bundle by ID."""
        result = await db.execute(
            select(ClaimBundle).where(ClaimBundle.claim_id == claim_id)
        )
        return result.scalar_one_or_none()

    async def validate_claim(
        self,
        db: AsyncSession,
        claim_id: str,
        pin: str,
        device_fingerprint: str,
        ip_address: str,
        user_agent: Optional[str] = None,
        wallet_address: Optional[str] = None,
    ) -> dict:
        """Validate a claim attempt with anti-double-claim, brute-force protection, and cooldown."""
        claim = await self.get_claim(db, claim_id)
        now = datetime.now(timezone.utc)

        # Log attempt first
        attempt = ClaimAttempt(
            claim_id=claim_id,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
        )
        db.add(attempt)

        if not claim:
            attempt.failure_reason = "not_found"
            await db.commit()
            return {"valid": False, "error": "claim_not_found", "message": "Claim not found"}

        # Update attempt count on claim bundle
        claim.attempt_count = (claim.attempt_count or 0) + 1
        claim.last_attempt_at = now
        await db.commit()

        # Check already claimed
        if claim.claimed:
            attempt.failure_reason = "already_claimed"
            await db.commit()
            return {
                "valid": False,
                "error": "already_claimed",
                "message": "This CoinPack has already been claimed",
                "claimed_at": claim.claimed_at.isoformat() if claim.claimed_at else None,
                "claimer": claim.claimer,
            }

        # Check expiration
        if now > claim.expires_at:
            attempt.failure_reason = "expired"
            await db.commit()
            return {
                "valid": False,
                "error": "expired",
                "message": "This CoinPack has expired",
                "expired_at": claim.expires_at.isoformat(),
            }

        # Check PIN attempts cooldown on claim bundle (stateful lockout)
        if (claim.attempt_count or 0) > settings.PIN_MAX_ATTEMPTS:
            cooldown_end = claim.last_attempt_at + timedelta(minutes=settings.PIN_LOCKOUT_MINUTES)
            if now < cooldown_end:
                remaining = int((cooldown_end - now).total_seconds())
                attempt.failure_reason = "too_many_attempts"
                await db.commit()
                return {
                    "valid": False,
                    "error": "too_many_attempts",
                    "message": f"Too many failed attempts. Try again in {remaining} seconds.",
                    "retry_after": remaining,
                }
            # Reset attempt count after cooldown expires
            claim.attempt_count = 1

        # Constant-time PIN comparison. Try modern salted+peppered hash first;
        # fall back to legacy unsalted SHA-256 only for pre-hardening claims.
        expected_hash = self._hash_pin(pin, claim.pin_salt)
        pin_valid = hmac.compare_digest(expected_hash, claim.pin_hash)
        if not pin_valid and claim.pin_salt == "":
            # Legacy migration path: unsalted SHA-256 for old claims
            expected_legacy = self._hash_pin_legacy(pin)
            pin_valid = hmac.compare_digest(expected_legacy, claim.pin_hash)

        if not pin_valid:
            attempt.failure_reason = "invalid_pin"
            await db.commit()
            return {
                "valid": False,
                "error": "invalid_pin",
                "message": "Invalid PIN",
                "attempts_remaining": max(0, settings.PIN_MAX_ATTEMPTS - (claim.attempt_count or 0)),
            }

        # Success — compute proof hash
        proof = hashlib.sha256(
            f"{claim_id}:{wallet_address or device_fingerprint}:{now.isoformat()}:{settings.CLAIM_LINK_SECRET}".encode()
        ).hexdigest()

        attempt.success = True
        claim.claimed = True
        claim.claimer = device_fingerprint
        claim.claimed_by_wallet = wallet_address
        claim.claimed_at = now
        claim.device_fingerprint = device_fingerprint
        claim.device_fingerprint_hash = hashlib.sha256(device_fingerprint.encode()).hexdigest()
        claim.proof_hash = proof

        await db.commit()

        # Audit log
        audit = AuditLog(
            event_type="claim_success",
            wallet_address=claim.creator,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "claim_id": claim_id,
                "device_fingerprint": device_fingerprint,
                "wallet_address": wallet_address,
                "assets": claim.asset_types,
                "amounts": claim.amounts,
            },
        )
        db.add(audit)
        await db.commit()

        return {
            "valid": True,
            "claim_id": claim_id,
            "assets": [
                {"type": t, "amount": a}
                for t, a in zip(claim.asset_types, claim.amounts)
            ],
            "claimed_at": claim.claimed_at.isoformat(),
            "proof_hash": proof,
        }

    async def verify_claim_integrity(self, db: AsyncSession, claim_id: str) -> bool:
        """Verify claim_id has not been tampered with using HMAC claim_hash."""
        claim = await self.get_claim(db, claim_id)
        if not claim:
            return False
        expected = self._generate_claim_hash(claim_id)
        return hmac.compare_digest(expected, claim.claim_hash)

    async def get_claim_stats(self, db: AsyncSession, claim_id: str) -> dict:
        """Get claim statistics and attempt history."""
        claim = await self.get_claim(db, claim_id)
        if not claim:
            return {"error": "not_found"}

        attempts_result = await db.execute(
            select(ClaimAttempt).where(ClaimAttempt.claim_id == claim_id)
        )
        attempts = attempts_result.scalars().all()

        return {
            "claim_id": claim_id,
            "claimed": claim.claimed,
            "total_attempts": len(attempts),
            "failed_attempts": len([a for a in attempts if not a.success]),
            "expires_at": claim.expires_at.isoformat(),
            "created_at": claim.created_at.isoformat(),
        }


# Global instance
claim_service = ClaimService()
