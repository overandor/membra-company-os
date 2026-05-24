"""ProofBook API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.db.base import get_db
from app.services.proofbook import ProofBookService
from app.schemas.proofbook import ProofBookEntryCreate, ProofChainCreate, DecisionEventCreate, SettlementEligibilityCreate
from app.schemas.common import BaseResponse, PaginatedResponse

router = APIRouter()


@router.post("/entries", response_model=BaseResponse)
def write_entry(data: ProofBookEntryCreate, db: Session = Depends(get_db)):
    svc = ProofBookService(db)
    entry = svc.write_entry(
        entry_type=data.entry_type,
        resource_type=data.resource_type,
        resource_id=data.resource_id,
        actor_type=data.actor_type,
        actor_id=data.actor_id,
        description=data.description,
        data=data.data,
        ipfs_cid=data.ipfs_cid,
        chain_id=data.chain_id,
        company_id=data.company_id,
    )
    return BaseResponse(data={"id": str(entry.id), "hash": entry.proof_hash})


@router.get("/entries", response_model=PaginatedResponse)
def list_entries(
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    svc = ProofBookService(db)
    if resource_type and resource_id:
        items = svc.get_entries_for_resource(resource_type, resource_id, limit)
    else:
        items = []
    return PaginatedResponse(
        items=[{"id": str(e.id), "type": e.entry_type.value, "hash": e.proof_hash} for e in items],
        total=len(items),
        page=1,
        page_size=limit,
        pages=1,
    )


@router.post("/chains", response_model=BaseResponse)
def create_chain(data: ProofChainCreate, db: Session = Depends(get_db)):
    svc = ProofBookService(db)
    chain = svc.create_chain(data)
    return BaseResponse(data={"id": str(chain.id), "genesis": chain.genesis_hash})


@router.get("/chains/{chain_id}/verify", response_model=BaseResponse)
def verify_chain(chain_id: str, db: Session = Depends(get_db)):
    svc = ProofBookService(db)
    result = svc.verify_chain_integrity(chain_id)
    return BaseResponse(data=result)


@router.post("/decisions", response_model=BaseResponse)
def record_decision(data: DecisionEventCreate, db: Session = Depends(get_db)):
    svc = ProofBookService(db)
    event = svc.record_decision(data)
    return BaseResponse(data={"id": str(event.id), "proof_hash": event.proof_hash})


@router.post("/eligibility", response_model=BaseResponse)
def create_eligibility(data: SettlementEligibilityCreate, db: Session = Depends(get_db)):
    svc = ProofBookService(db)
    elig = svc.create_eligibility(data)
    return BaseResponse(data={"id": str(elig.id), "amount": elig.eligible_amount, "status": elig.status})


@router.get("/subject/{subject_type}/{subject_id}", response_model=PaginatedResponse)
def get_subject_entries(
    subject_type: str,
    subject_id: str,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    from uuid import UUID as PyUUID
    from app.models.proofbook import ProofBookEntry
    entries = db.query(ProofBookEntry).filter(
        ProofBookEntry.resource_type == subject_type,
        ProofBookEntry.resource_id == PyUUID(subject_id)
    ).order_by(ProofBookEntry.created_at.desc()).limit(limit).all()
    return PaginatedResponse(
        items=[{
            "id": str(e.id),
            "entry_type": e.entry_type.value if e.entry_type else None,
            "actor_type": e.actor_type,
            "actor_id": str(e.actor_id) if e.actor_id else None,
            "proof_hash": e.proof_hash,
            "previous_hash": e.previous_hash,
            "description": e.description,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        } for e in entries],
        total=len(entries),
        page=1,
        page_size=limit,
        pages=1,
    )
