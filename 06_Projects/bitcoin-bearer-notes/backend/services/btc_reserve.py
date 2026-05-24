"""BTC Reserve tracking and proof-of-reserves."""
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Optional, List, Dict
import httpx

from core.config import settings
from models.database import ReserveAccount, ReserveSnapshot, Liability
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func


class BTCReserveService:
    """Tracks BTC reserves backing the bearer notes."""

    def __init__(self):
        self.mempool_api = settings.MEMPOOL_API_BASE
        self.network = settings.BTC_NETWORK

    async def get_address_balance(self, address: str) -> dict:
        """Get confirmed and unconfirmed balance for a BTC address."""
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"{self.mempool_api}/address/{address}",
                    timeout=30.0
                )
                resp.raise_for_status()
                data = resp.json()

                chain_stats = data.get("chain_stats", {})
                mempool_stats = data.get("mempool_stats", {})

                funded = chain_stats.get("funded_txo_sum", 0)
                spent = chain_stats.get("spent_txo_sum", 0)
                confirmed = funded - spent

                pending_funded = mempool_stats.get("funded_txo_sum", 0)
                pending_spent = mempool_stats.get("spent_txo_sum", 0)
                pending = pending_funded - pending_spent

                return {
                    "address": address,
                    "confirmed_sats": confirmed,
                    "pending_sats": pending,
                    "total_sats": confirmed + pending,
                    "tx_count": chain_stats.get("tx_count", 0),
                    "block_height": await self.get_block_height(),
                }
            except Exception as e:
                return {
                    "address": address,
                    "error": str(e),
                    "confirmed_sats": 0,
                    "pending_sats": 0,
                    "total_sats": 0,
                }

    async def get_block_height(self) -> int:
        """Get current BTC block height."""
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"{self.mempool_api}/blocks/tip/height",
                    timeout=10.0
                )
                return int(resp.text)
            except:
                return 0

    async def verify_reserves(
        self,
        reserve_addresses: List[str],
        required_sats: int
    ) -> dict:
        """Verify total reserves cover all minted notes."""
        total = 0
        per_address = []

        for addr in reserve_addresses:
            bal = await self.get_address_balance(addr)
            sats = bal.get("total_sats", 0)
            total += sats
            per_address.append({
                "address": addr,
                "balance_sats": sats,
            })

        shortfall = max(0, required_sats - total)
        overcollateralized = total - required_sats

        return {
            "verified_at": datetime.utcnow().isoformat(),
            "total_reserved_sats": total,
            "total_required_sats": required_sats,
            "shortfall_sats": shortfall,
            "overcollateralized_sats": overcollateralized,
            "fully_backed": shortfall == 0,
            "reserve_ratio": total / required_sats if required_sats > 0 else 1.0,
            "addresses": per_address,
        }

    def generate_proof_of_reserves(
        self,
        reserve_addresses: List[str],
        message: str
    ) -> str:
        """Generate a proof-of-reserves message hash."""
        data = message + ":" + ":".join(sorted(reserve_addresses))
        return hashlib.sha256(data.encode()).hexdigest()

    def verify_proof(
        self,
        message: str,
        addresses: List[str],
        expected_hash: str
    ) -> bool:
        """Verify a proof-of-reserves hash."""
        computed = self.generate_proof_of_reserves(addresses, message)
        return hmac.compare_digest(computed, expected_hash)

    async def create_snapshot(
        self,
        db: AsyncSession,
        reserve_account_id: int,
        liabilities_sats: int,
    ) -> Optional[ReserveSnapshot]:
        """Create a reserve snapshot from live mempool data."""
        account_result = await db.execute(
            select(ReserveAccount).where(ReserveAccount.id == reserve_account_id)
        )
        account = account_result.scalar_one_or_none()
        if not account or account.status != "active":
            return None

        bal = await self.get_address_balance(account.address)
        observed = bal.get("total_sats", 0)
        block_height = bal.get("block_height", 0)

        ratio_bps = 0
        if liabilities_sats > 0:
            ratio_bps = int((observed / liabilities_sats) * 10000)

        proof = hashlib.sha256(
            f"{account.address}:{observed}:{liabilities_sats}:{block_height}:{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()

        snapshot = ReserveSnapshot(
            reserve_account_id=reserve_account_id,
            observed_balance_sats=observed,
            liabilities_sats=liabilities_sats,
            reserve_ratio_bps=ratio_bps,
            block_height=block_height,
            source="mempool.space",
            proof_hash=proof,
        )
        db.add(snapshot)
        await db.commit()
        await db.refresh(snapshot)
        return snapshot

    async def get_latest_proof(
        self,
        db: AsyncSession,
        asset: str = "BTC",
    ) -> dict:
        """Get the latest reserve proof with disclaimer."""
        accounts_result = await db.execute(
            select(ReserveAccount).where(
                ReserveAccount.asset == asset,
                ReserveAccount.status == "active",
            )
        )
        accounts = accounts_result.scalars().all()

        total_observed = 0
        snapshots = []
        degraded = False

        for account in accounts:
            snap_result = await db.execute(
                select(ReserveSnapshot)
                .where(ReserveSnapshot.reserve_account_id == account.id)
                .order_by(ReserveSnapshot.created_at.desc())
                .limit(1)
            )
            snap = snap_result.scalar_one_or_none()
            if snap:
                total_observed += snap.observed_balance_sats
                snapshots.append({
                    "address": account.address,
                    "wallet_type": account.wallet_type,
                    "observed_sats": snap.observed_balance_sats,
                    "block_height": snap.block_height,
                    "source": snap.source,
                    "proof_hash": snap.proof_hash,
                    "created_at": snap.created_at.isoformat() if snap.created_at else None,
                })
            else:
                degraded = True

        liabilities_result = await db.execute(
            select(func.sum(Liability.amount_sats_or_units)).where(
                Liability.asset == asset,
                Liability.status == "outstanding",
            )
        )
        liabilities_sats = liabilities_result.scalar() or 0

        ratio_bps = 0
        if liabilities_sats > 0:
            ratio_bps = int((total_observed / liabilities_sats) * 10000)

        fully_backed = ratio_bps >= 10000 and not degraded
        can_mint = ratio_bps >= settings.MIN_RESERVE_RATIO_BPS and not degraded

        return {
            "asset": asset,
            "reserve_balance_sats": total_observed,
            "outstanding_liabilities_sats": liabilities_sats,
            "reserve_ratio_bps": ratio_bps,
            "fully_backed": fully_backed,
            "can_mint_new_notes": can_mint,
            "degraded_source": degraded,
            "snapshots": snapshots,
            "disclaimer": "Reserve data is informational and depends on configured reserve source.",
        }


class RedemptionProcessor:
    """Processes BTC redemptions from burned notes."""

    def __init__(self):
        self.btc_service = BTCReserveService()
        self.network = settings.BTC_NETWORK

    async def validate_btc_address(self, address: str) -> bool:
        """Basic BTC address validation."""
        if not address or len(address) < 26 or len(address) > 74:
            return False

        # Bech32 (bc1...)
        if address.startswith("bc1") or address.startswith("tb1"):
            return len(address) in [42, 62]

        # Legacy (1... or 2... or 3...)
        if address[0] in "123":
            return True

        return False

    async def estimate_fee(self, sats_per_vbyte: int = 20) -> dict:
        """Estimate BTC transaction fee for redemption."""
        # P2WPKH input ~68 vbytes, P2WPKH output ~31 vbytes
        # 1 input, 1 output, change output = ~141 vbytes
        tx_vbytes = 141
        fee_sats = tx_vbytes * sats_per_vbyte

        return {
            "fee_sats": fee_sats,
            "fee_btc": fee_sats / 1e8,
            "sats_per_vbyte": sats_per_vbyte,
            "tx_vbytes": tx_vbytes,
        }

    async def queue_redemption(
        self,
        serial_number: int,
        btc_address: str,
        denomination_sats: int,
    ) -> dict:
        """Queue a redemption for batch processing."""
        fee = await self.estimate_fee()
        net_amount = max(0, denomination_sats - fee["fee_sats"])

        return {
            "status": "queued",
            "serial_number": serial_number,
            "btc_address": btc_address,
            "gross_amount_sats": denomination_sats,
            "estimated_fee_sats": fee["fee_sats"],
            "net_amount_sats": net_amount,
            "estimated_confirmation": "30-60 minutes",
            "queue_position": 1,  # Would be from Redis queue
        }


# Global instance
btc_reserve_service = BTCReserveService()
redemption_processor = RedemptionProcessor()
