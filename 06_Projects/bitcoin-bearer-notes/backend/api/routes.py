"""FastAPI routes for CoinPack redemption API."""
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timezone
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.database import (
    get_db, NoteRecord, ClaimBundle, RedemptionRequest,
    BTCReserveBalance, AuditLog, ReserveAccount, ReserveSnapshot, Liability,
    RiskDisclosureAcceptance,
)
from services.btc_reserve import btc_reserve_service, redemption_processor
from services.claim_service import claim_service
from services.risk_disclosure import risk_service
from services.delivery import get_delivery_provider

router = APIRouter(prefix="/api/v1")
delivery_provider = get_delivery_provider()


# ============== SCHEMAS ==============

class MintNoteRequest(BaseModel):
    denomination: int = Field(..., ge=1000000000, le=50000000000)
    metadata_uri: str = Field(default="", max_length=200)
    holder: str = Field(..., min_length=32, max_length=44)


class TransferNoteRequest(BaseModel):
    serial_number: int
    new_holder: str = Field(..., min_length=32, max_length=44)
    holder: str = Field(..., min_length=32, max_length=44)


class RedeemRequest(BaseModel):
    serial_number: int
    btc_address: str = Field(..., min_length=26, max_length=74)
    holder: str = Field(..., min_length=32, max_length=44)
    accepted_risk_disclosure: bool = Field(default=False)


class ClaimCreateRequest(BaseModel):
    creator: str = Field(..., min_length=32, max_length=44)
    assets: List[Dict[str, float]] = Field(..., min_length=1, max_length=5)
    pin: str = Field(..., min_length=4, max_length=8)
    expires_hours: int = Field(default=24, ge=1, le=168)
    delivery_method: str = Field(default="link")
    delivery_address: Optional[str] = None


class ClaimVerifyRequest(BaseModel):
    pin: str = Field(..., min_length=4, max_length=8)
    device_fingerprint: str = Field(..., min_length=10, max_length=128)
    wallet_address: Optional[str] = None


class ClaimRedeemRequest(BaseModel):
    claim_id: str = Field(..., min_length=32, max_length=64)
    pin: str = Field(..., min_length=4, max_length=8)
    device_fingerprint: str = Field(..., min_length=10, max_length=128)
    wallet_address: Optional[str] = None
    accepted_risk_disclosure: bool = Field(default=False)


class ReserveCheckRequest(BaseModel):
    reserve_addresses: List[str]
    required_sats: int


class RedemptionProcessRequest(BaseModel):
    status: str = Field(..., pattern="^(processing|completed|failed|rejected)$")
    txid: Optional[str] = None
    actual_fee: Optional[int] = None


class RiskDisclosureAcceptRequest(BaseModel):
    wallet_address: str = Field(..., min_length=32, max_length=44)
    claim_id: Optional[str] = None
    accepted: bool = Field(default=False)


# ============== MIDDLEWARE HELPERS ==============

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


# ============== HEALTH ==============

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "membra-api",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(select(func.count(NoteRecord.id)))
        return {"status": "ready", "database": "connected"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database not ready")


# ============== NOTES ==============

@router.get("/notes")
async def list_notes(
    holder: Optional[str] = None,
    redeemed: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """List bearer notes with optional filtering."""
    query = select(NoteRecord)
    if holder:
        query = query.where(NoteRecord.current_holder == holder)
    if redeemed is not None:
        query = query.where(NoteRecord.redeemed == redeemed)

    result = await db.execute(query)
    notes = result.scalars().all()

    return {
        "count": len(notes),
        "notes": [
            {
                "serial_number": n.serial_number,
                "denomination": n.denomination,
                "holder": n.current_holder,
                "redeemed": n.redeemed,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notes
        ],
    }


@router.get("/notes/{serial_number}")
async def get_note(serial_number: int, db: AsyncSession = Depends(get_db)):
    """Get a specific note by serial number."""
    result = await db.execute(
        select(NoteRecord).where(NoteRecord.serial_number == serial_number)
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return {
        "serial_number": note.serial_number,
        "denomination": note.denomination,
        "denomination_btc": note.denomination / 1e8,
        "mint_authority": note.mint_authority,
        "current_holder": note.current_holder,
        "original_holder": note.original_holder,
        "metadata_uri": note.metadata_uri,
        "created_at": note.created_at.isoformat() if note.created_at else None,
        "expires_at": note.expires_at.isoformat() if note.expires_at else None,
        "redeemed": note.redeemed,
        "redeemed_at": note.redeemed_at.isoformat() if note.redeemed_at else None,
        "btc_receiving_address": note.btc_receiving_address,
        "revoked": note.revoked,
    }


@router.post("/notes/{serial_number}/transfer")
async def transfer_note(
    serial_number: int,
    req: TransferNoteRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Transfer a note to a new holder (requires holder signature)."""
    result = await db.execute(
        select(NoteRecord).where(
            and_(
                NoteRecord.serial_number == serial_number,
                NoteRecord.redeemed == False,
                NoteRecord.revoked == False,
            )
        )
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found or already spent")
    if note.current_holder != req.holder:
        raise HTTPException(status_code=403, detail="Not the note holder")

    previous_holder = note.current_holder
    note.current_holder = req.new_holder
    await db.commit()

    # Audit log
    audit = AuditLog(
        event_type="note_transferred",
        wallet_address=req.holder,
        ip_address=get_client_ip(request),
        details={
            "serial_number": serial_number,
            "from": previous_holder,
            "to": req.new_holder,
        },
    )
    db.add(audit)
    await db.commit()

    return {
        "status": "transferred",
        "serial_number": serial_number,
        "from": previous_holder,
        "to": req.new_holder,
        "transferred_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/notes/{serial_number}/burn-to-redeem")
async def burn_to_redeem(
    serial_number: int,
    req: RedeemRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Burn a note and queue BTC redemption."""
    if not req.accepted_risk_disclosure:
        raise HTTPException(status_code=400, detail="Risk disclosure must be accepted")

    result = await db.execute(
        select(NoteRecord).where(NoteRecord.serial_number == serial_number)
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.redeemed:
        raise HTTPException(status_code=400, detail="Note already redeemed")
    if note.current_holder != req.holder:
        raise HTTPException(status_code=403, detail="Not the note holder")

    if not await redemption_processor.validate_btc_address(req.btc_address):
        raise HTTPException(status_code=400, detail="Invalid BTC address")

    # Mark as redeemed
    note.redeemed = True
    note.redeemed_at = datetime.now(timezone.utc)
    note.btc_receiving_address = req.btc_address
    await db.commit()

    # Queue redemption
    queue_info = await redemption_processor.queue_redemption(
        serial_number,
        req.btc_address,
        note.denomination,
    )

    # Create redemption record
    redemption = RedemptionRequest(
        serial_number=serial_number,
        holder=req.holder,
        btc_address=req.btc_address,
        denomination=note.denomination,
        status="queued",
        estimated_fee=queue_info["estimated_fee_sats"],
    )
    db.add(redemption)
    await db.commit()
    await db.refresh(redemption)

    # Audit log
    audit = AuditLog(
        event_type="note_redeemed",
        wallet_address=req.holder,
        ip_address=get_client_ip(request),
        details={
            "serial_number": serial_number,
            "btc_address": req.btc_address,
            "denomination": note.denomination,
            "queue_position": queue_info["queue_position"],
        },
    )
    db.add(audit)
    await db.commit()

    return {
        "status": "redeemed",
        "serial_number": serial_number,
        "btc_address": req.btc_address,
        "net_amount_sats": queue_info["net_amount_sats"],
        "estimated_fee_sats": queue_info["estimated_fee_sats"],
        "estimated_confirmation": queue_info["estimated_confirmation"],
    }


@router.get("/notes/{serial_number}/status")
async def note_status(serial_number: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(NoteRecord).where(NoteRecord.serial_number == serial_number)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    redemption_result = await db.execute(
        select(RedemptionRequest).where(RedemptionRequest.serial_number == serial_number)
    )
    redemption = redemption_result.scalar_one_or_none()

    return {
        "serial_number": note.serial_number,
        "status": "redeemed" if note.redeemed else "active",
        "holder": note.current_holder,
        "redeemed_at": note.redeemed_at.isoformat() if note.redeemed_at else None,
        "redemption_status": redemption.status if redemption else None,
        "redemption_txid": redemption.txid if redemption else None,
    }


# ============== COINPACK CLAIMS ==============

@router.post("/claims")
async def create_claim(
    req: ClaimCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Create a new CoinPack claim bundle."""
    result = await claim_service.create_claim(
        db=db,
        creator=req.creator,
        assets=req.assets,
        pin=req.pin,
        expires_hours=req.expires_hours,
        delivery_method=req.delivery_method,
        delivery_address=req.delivery_address,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )

    # Attempt delivery if address provided
    if req.delivery_address:
        await delivery_provider.send_claim_link(
            destination=req.delivery_address,
            claim_url=result["claim_url"],
            pin=req.pin,
            expires_at=result["expires_at"],
            assets=req.assets,
        )

    return result


@router.get("/claims/{claim_id}")
async def get_claim(claim_id: str, db: AsyncSession = Depends(get_db)):
    """Get claim bundle info (without PIN)."""
    claim = await claim_service.get_claim(db, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    return {
        "claim_id": claim.claim_id,
        "claimed": claim.claimed,
        "expires_at": claim.expires_at.isoformat(),
        "created_at": claim.created_at.isoformat() if claim.created_at else None,
        "asset_count": len(claim.asset_types),
        "assets": [
            {"type": t, "amount": a}
            for t, a in zip(claim.asset_types, claim.amounts)
        ],
    }


@router.post("/coinpacks/{claim_id}/verify")
async def verify_claim(
    claim_id: str,
    req: ClaimVerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Verify a claim without consuming it (check PIN only)."""
    claim = await claim_service.get_claim(db, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    if claim.claimed:
        raise HTTPException(status_code=400, detail="Already claimed")
    if datetime.now(timezone.utc) > claim.expires_at:
        raise HTTPException(status_code=400, detail="Claim expired")

    expected = claim_service._hash_pin(req.pin, claim.pin_salt)
    import hmac
    if not hmac.compare_digest(expected, claim.pin_hash):
        raise HTTPException(status_code=400, detail="Invalid PIN")

    return {
        "claimable": True,
        "assets": [
            {"type": t, "amount": a}
            for t, a in zip(claim.asset_types, claim.amounts)
        ],
        "expires_at": claim.expires_at.isoformat(),
        "risk_disclosure_required": True,
    }


@router.post("/coinpacks/{claim_id}/claim")
async def claim_coinpack(
    claim_id: str,
    req: ClaimRedeemRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Claim a CoinPack with PIN, device fingerprint, and risk disclosure."""
    if not req.accepted_risk_disclosure:
        raise HTTPException(status_code=400, detail="Risk disclosure must be accepted")

    # Record disclosure acceptance
    if req.wallet_address:
        has_accepted = await risk_service.has_accepted(db, req.wallet_address, claim_id)
        if not has_accepted:
            await risk_service.record_acceptance(
                db, req.wallet_address, claim_id,
                ip_address=get_client_ip(request),
                user_agent=request.headers.get("User-Agent"),
            )

    result = await claim_service.validate_claim(
        db=db,
        claim_id=claim_id,
        pin=req.pin,
        device_fingerprint=req.device_fingerprint,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        wallet_address=req.wallet_address,
    )

    if not result["valid"]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": result["error"],
                "message": result["message"],
                "retry_after": result.get("retry_after"),
            },
        )

    return result


@router.post("/coinpacks/{claim_id}/expire")
async def expire_claim(claim_id: str, db: AsyncSession = Depends(get_db)):
    """Manually expire a claim (admin or creator only)."""
    claim = await claim_service.get_claim(db, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    claim.expires_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": "expired", "claim_id": claim_id}


# ============== REDEMPTIONS ==============

@router.post("/redemptions")
async def list_redemptions(
    holder: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(RedemptionRequest)
    if holder:
        query = query.where(RedemptionRequest.holder == holder)
    if status:
        query = query.where(RedemptionRequest.status == status)

    result = await db.execute(query)
    redemptions = result.scalars().all()
    return {
        "count": len(redemptions),
        "redemptions": [
            {
                "id": r.id,
                "serial_number": r.serial_number,
                "holder": r.holder,
                "btc_address": r.btc_address,
                "status": r.status,
                "txid": r.txid,
                "requested_at": r.requested_at.isoformat() if r.requested_at else None,
            }
            for r in redemptions
        ],
    }


@router.get("/redemptions/{redemption_id}")
async def get_redemption(redemption_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RedemptionRequest).where(RedemptionRequest.id == redemption_id)
    )
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Redemption not found")
    return {
        "id": r.id,
        "serial_number": r.serial_number,
        "holder": r.holder,
        "btc_address": r.btc_address,
        "denomination": r.denomination,
        "status": r.status,
        "txid": r.txid,
        "estimated_fee": r.estimated_fee,
        "actual_fee": r.actual_fee,
        "requested_at": r.requested_at.isoformat() if r.requested_at else None,
        "processed_at": r.processed_at.isoformat() if r.processed_at else None,
    }


@router.post("/redemptions/{redemption_id}/process")
async def process_redemption(
    redemption_id: int,
    req: RedemptionProcessRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RedemptionRequest).where(RedemptionRequest.id == redemption_id)
    )
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Redemption not found")

    r.status = req.status
    if req.txid:
        r.txid = req.txid
    if req.actual_fee is not None:
        r.actual_fee = req.actual_fee
    r.processed_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": "updated", "redemption_id": redemption_id, "new_status": req.status}


@router.post("/redemptions/{redemption_id}/mark-paid")
async def mark_redemption_paid(redemption_id: int, db: AsyncSession = Depends(get_db)):
    return await process_redemption(redemption_id, RedemptionProcessRequest(status="completed"), db)


@router.post("/redemptions/{redemption_id}/reject")
async def reject_redemption(redemption_id: int, db: AsyncSession = Depends(get_db)):
    return await process_redemption(redemption_id, RedemptionProcessRequest(status="rejected"), db)


# ============== BTC RESERVES ==============

@router.get("/reserves")
async def get_reserves(db: AsyncSession = Depends(get_db)):
    """Get current BTC reserve status with disclaimer."""
    proof = await btc_reserve_service.get_latest_proof(db, asset="BTC")
    return proof


@router.get("/reserves/proof")
async def get_reserve_proof(db: AsyncSession = Depends(get_db)):
    """Get latest proof-of-reserves with snapshots."""
    return await btc_reserve_service.get_latest_proof(db, asset="BTC")


@router.post("/reserves/snapshot")
async def create_reserve_snapshot(
    reserve_account_id: int,
    db: AsyncSession = Depends(get_db),
):
    liabilities_result = await db.execute(
        select(func.sum(Liability.amount_sats_or_units)).where(
            Liability.asset == "BTC",
            Liability.status == "outstanding",
        )
    )
    liabilities_sats = liabilities_result.scalar() or 0
    snapshot = await btc_reserve_service.create_snapshot(db, reserve_account_id, liabilities_sats)
    if not snapshot:
        raise HTTPException(status_code=400, detail="Could not create snapshot")
    return {
        "snapshot_id": snapshot.id,
        "observed_sats": snapshot.observed_balance_sats,
        "liabilities_sats": snapshot.liabilities_sats,
        "ratio_bps": snapshot.reserve_ratio_bps,
    }


@router.post("/reserves/verify")
async def verify_reserves(req: ReserveCheckRequest):
    result = await btc_reserve_service.verify_reserves(
        req.reserve_addresses,
        req.required_sats,
    )
    return result


@router.get("/reserves/balance/{address}")
async def get_address_balance(address: str):
    result = await btc_reserve_service.get_address_balance(address)
    return result


# ============== AUDIT ==============

@router.get("/audit/events")
async def list_audit_events(
    event_type: Optional[str] = None,
    wallet_address: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    query = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if event_type:
        query = query.where(AuditLog.event_type == event_type)
    if wallet_address:
        query = query.where(AuditLog.wallet_address == wallet_address)

    result = await db.execute(query)
    events = result.scalars().all()
    return {
        "count": len(events),
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "wallet_address": e.wallet_address,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "details": e.details,
            }
            for e in events
        ],
    }


@router.get("/audit/subject/{subject_type}/{subject_id}")
async def audit_by_subject(
    subject_type: str,
    subject_id: str,
    db: AsyncSession = Depends(get_db),
):
    if subject_type == "note":
        query = select(AuditLog).where(
            AuditLog.details["serial_number"].as_string() == subject_id
        )
    elif subject_type == "claim":
        query = select(AuditLog).where(
            AuditLog.details["claim_id"].as_string() == subject_id
        )
    else:
        raise HTTPException(status_code=400, detail="Unknown subject type")

    result = await db.execute(query.order_by(AuditLog.created_at.desc()))
    events = result.scalars().all()
    return {"subject_type": subject_type, "subject_id": subject_id, "events": [
        {"id": e.id, "event_type": e.event_type, "created_at": e.created_at.isoformat() if e.created_at else None}
        for e in events
    ]}


# ============== RISK DISCLOSURE ==============

@router.get("/risk-disclosures/current")
async def get_current_risk_disclosure():
    return {
        "version": risk_service.current_version(),
        "hash": risk_service.current_hash(),
        "text": risk_service.current_text(),
    }


@router.post("/risk-disclosures/accept")
async def accept_risk_disclosure(
    req: RiskDisclosureAcceptRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    if not req.accepted:
        raise HTTPException(status_code=400, detail="Must accept disclosure")
    acceptance = await risk_service.record_acceptance(
        db,
        wallet_address=req.wallet_address,
        claim_id=req.claim_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return {
        "status": "accepted",
        "wallet_address": req.wallet_address,
        "version": acceptance.disclosure_version,
        "accepted_at": acceptance.accepted_at.isoformat() if acceptance.accepted_at else None,
    }


# ============== STATS ==============

@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    notes_count = await db.execute(select(func.count(NoteRecord.id)))
    redeemed_count = await db.execute(
        select(func.count(NoteRecord.id)).where(NoteRecord.redeemed == True)
    )
    claims_count = await db.execute(select(func.count(ClaimBundle.id)))
    claimed_count = await db.execute(
        select(func.count(ClaimBundle.id)).where(ClaimBundle.claimed == True)
    )
    liabilities_result = await db.execute(
        select(func.sum(Liability.amount_sats_or_units)).where(
            Liability.asset == "BTC",
            Liability.status == "outstanding",
        )
    )

    return {
        "total_notes": notes_count.scalar(),
        "redeemed_notes": redeemed_count.scalar(),
        "total_claims": claims_count.scalar(),
        "claimed_claims": claimed_count.scalar(),
        "outstanding_liabilities_sats": liabilities_result.scalar() or 0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
