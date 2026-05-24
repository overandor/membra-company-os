"""SettlementOS API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.base import get_db
from app.services.settlement import SettlementService
from app.schemas.settlement import SettlementRecordCreate, SettlementRecordRead, PayoutInstructionCreate, ExternalRailLogCreate
from app.schemas.common import BaseResponse, PaginatedResponse

router = APIRouter()


@router.post("/records", response_model=BaseResponse)
def create_record(data: SettlementRecordCreate, db: Session = Depends(get_db)):
    svc = SettlementService(db)
    record = svc.create_record(data)
    return BaseResponse(data={"id": str(record.id), "status": record.status.value, "rail": record.rail.value})


@router.get("/records", response_model=PaginatedResponse)
def list_records(
    company_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    svc = SettlementService(db)
    items = svc.list_settlements(company_id=company_id, status=status, limit=limit)
    return PaginatedResponse(
        items=[{"id": str(r.id), "status": r.status.value, "amount": float(r.amount), "rail": r.rail.value} for r in items],
        total=len(items),
        page=1,
        page_size=limit,
        pages=1,
    )


@router.post("/records/{settlement_id}/instructions", response_model=BaseResponse)
def send_instructions(settlement_id: str, instructions: List[PayoutInstructionCreate], db: Session = Depends(get_db)):
    svc = SettlementService(db)
    record = svc.send_instructions(settlement_id, instructions)
    return BaseResponse(data={"id": str(record.id), "status": record.status.value})


@router.post("/records/{settlement_id}/settled", response_model=BaseResponse)
def mark_settled(settlement_id: str, external_tx_id: Optional[str] = None, db: Session = Depends(get_db)):
    svc = SettlementService(db)
    record = svc.mark_settled(settlement_id, external_tx_id)
    return BaseResponse(data={"id": str(record.id), "status": record.status.value, "tx_id": record.external_tx_id})


@router.post("/rail-logs", response_model=BaseResponse)
def log_rail_event(data: ExternalRailLogCreate, db: Session = Depends(get_db)):
    svc = SettlementService(db)
    log = svc.log_rail_event(data)
    return BaseResponse(data={"id": str(log.id), "event": log.event_type})
