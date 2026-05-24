"""GovernanceOS API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.base import get_db
from app.services.governance import GovernanceService
from app.schemas.governance import ApprovalGateCreate, PolicyCreate, ConsentRecordCreate, RiskClassificationCreate, EscalationRuleCreate
from app.schemas.common import BaseResponse, PaginatedResponse

router = APIRouter()


@router.post("/approval-gates", response_model=BaseResponse)
def create_gate(data: ApprovalGateCreate, db: Session = Depends(get_db)):
    svc = GovernanceService(db)
    gate = svc.create_gate(data)
    return BaseResponse(data={"id": str(gate.id), "status": gate.status.value})


@router.get("/approval-gates", response_model=PaginatedResponse)
def list_gates(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    svc = GovernanceService(db)
    items = svc.list_gates(status=status, limit=limit)
    return PaginatedResponse(
        items=[{"id": str(g.id), "type": g.gate_type, "status": g.status.value} for g in items],
        total=len(items),
        page=1,
        page_size=limit,
        pages=1,
    )


@router.post("/approval-gates/{gate_id}/approve", response_model=BaseResponse)
def approve_gate(gate_id: str, approver_id: str, notes: Optional[str] = None, db: Session = Depends(get_db)):
    svc = GovernanceService(db)
    gate = svc.approve(gate_id, approver_id, notes)
    return BaseResponse(data={"id": str(gate.id), "status": gate.status.value, "approvals": gate.current_approvals})


@router.post("/approval-gates/{gate_id}/reject", response_model=BaseResponse)
def reject_gate(gate_id: str, approver_id: str, notes: Optional[str] = None, db: Session = Depends(get_db)):
    svc = GovernanceService(db)
    gate = svc.reject(gate_id, approver_id, notes)
    return BaseResponse(data={"id": str(gate.id), "status": gate.status.value})


@router.post("/policies", response_model=BaseResponse)
def create_policy(data: PolicyCreate, db: Session = Depends(get_db)):
    svc = GovernanceService(db)
    policy = svc.create_policy(data)
    return BaseResponse(data={"id": str(policy.id), "version": policy.version, "status": policy.status.value})


@router.post("/consent", response_model=BaseResponse)
def record_consent(data: ConsentRecordCreate, db: Session = Depends(get_db)):
    svc = GovernanceService(db)
    consent = svc.record_consent(data)
    return BaseResponse(data={"id": str(consent.id), "granted": consent.granted})


@router.post("/risk", response_model=BaseResponse)
def classify_risk(data: RiskClassificationCreate, db: Session = Depends(get_db)):
    svc = GovernanceService(db)
    risk = svc.classify_risk(data)
    return BaseResponse(data={"id": str(risk.id), "level": risk.risk_level.value})


@router.post("/escalation-rules", response_model=BaseResponse)
def create_escalation_rule(data: EscalationRuleCreate, db: Session = Depends(get_db)):
    svc = GovernanceService(db)
    rule = svc.create_escalation_rule(data)
    return BaseResponse(data={"id": str(rule.id), "name": rule.name, "active": rule.is_active})
