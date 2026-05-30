"""
CollateralOps — REST API routes for the execution desk.
T1-T8 implementation: Asset Register, Valuation, Proofs, Packet, Evidence, Import/Export.
"""
import csv
import hashlib
import io
import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

from models import (
    get_session,
    Asset, AssetType, AssetStatus,
    ValuationSet, ProofEvent, RiskFlag,
    PacketSection, BuyerTarget, AgentWorkRecord,
    ImprovementTask, AuditLog,
)

router = APIRouter(prefix="/api", tags=["collateral"])


# ─── Pydantic Schemas ───────────────────────────────────────────

class AssetCreate(BaseModel):
    name: str
    type: str = "repo"
    status: str = "active"
    strategic_value: float = 0.0
    buyer_today_value: float = 0.0
    liquidation_value: float = 0.0
    collateral_support: float = 0.0
    financeability_score: float = 0.0
    risk_score: float = 0.0
    lines_of_code: int = 0
    tech_stack: List[str] = Field(default_factory=list)
    repo_url: Optional[str] = None
    owner: Optional[str] = None


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    strategic_value: Optional[float] = None
    buyer_today_value: Optional[float] = None
    liquidation_value: Optional[float] = None
    collateral_support: Optional[float] = None
    financeability_score: Optional[float] = None
    risk_score: Optional[float] = None
    lines_of_code: Optional[int] = None
    tech_stack: Optional[List[str]] = None
    repo_url: Optional[str] = None
    owner: Optional[str] = None


class AssetOut(BaseModel):
    id: str
    name: str
    type: str
    status: str
    strategic_value: float
    buyer_today_value: float
    liquidation_value: float
    collateral_support: float
    financeability_score: float
    risk_score: float
    lines_of_code: int
    last_commit: Optional[str]
    tech_stack: List[str]
    repo_url: Optional[str]
    owner: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ValuationCreate(BaseModel):
    method: str
    value: float
    confidence: float = 0.0
    details: dict = Field(default_factory=dict)


class ProofCreate(BaseModel):
    event_type: str
    description: str
    metadata: dict = Field(default_factory=dict)


class RiskCreate(BaseModel):
    category: str
    severity: str = "medium"
    reason: str
    remediation: Optional[str] = None


class PacketSectionUpdate(BaseModel):
    is_complete: Optional[bool] = None
    completeness: Optional[float] = None
    evidence_count: Optional[int] = None


class BuyerCreate(BaseModel):
    name: str
    category: str
    probability: float = 0.0
    estimated_recovery: float = 0.0
    rationale: Optional[str] = None


class AgentWorkCreate(BaseModel):
    agent_name: str
    action: str
    files_created: int = 0
    files_modified: int = 0
    tests_added: int = 0
    docs_added: int = 0
    lines_added: int = 0
    lines_deleted: int = 0
    build_status: str = "unknown"
    duration_minutes: float = 0.0


class ImprovementCreate(BaseModel):
    title: str
    category: str
    impact_estimate: float = 0.0
    effort_estimate: str = "medium"
    priority: int = 0


class FinanceabilityResult(BaseModel):
    asset_id: str
    asset_name: str
    score: float
    components: dict
    deductions: List[dict]


# ─── Helpers ────────────────────────────────────────────────────

def _hash(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def _log(session, event_type: str, entity_type: str, entity_id: str, payload: dict):
    last = session.query(AuditLog).order_by(AuditLog.created_at.desc()).first()
    prev = last.hash if last else "0" * 64
    payload_json = json.dumps(payload, sort_keys=True, default=str)
    h = _hash(f"{event_type}:{entity_type}:{entity_id}:{payload_json}:{prev}")
    log = AuditLog(
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        payload=payload,
        hash=h,
        prev_hash=prev,
    )
    session.add(log)
    session.commit()


def _asset_to_dict(a: Asset) -> dict:
    return {
        "id": a.id,
        "name": a.name,
        "type": a.type.value if a.type else "repo",
        "status": a.status.value if a.status else "active",
        "strategic_value": a.strategic_value,
        "buyer_today_value": a.buyer_today_value,
        "liquidation_value": a.liquidation_value,
        "collateral_support": a.collateral_support,
        "financeability_score": a.financeability_score,
        "risk_score": a.risk_score,
        "lines_of_code": a.lines_of_code,
        "last_commit": a.last_commit.isoformat() if a.last_commit else None,
        "tech_stack": a.tech_stack or [],
        "repo_url": a.repo_url,
        "owner": a.owner,
        "created_at": a.created_at.isoformat(),
        "updated_at": a.updated_at.isoformat(),
    }


def _compute_financeability(asset: Asset) -> dict:
    """Weighted financeability scoring."""
    comps = {
        "ownership_clarity": min(100, max(0, 100 - len([r for r in asset.risks if r.category == "ownership" and not r.is_resolved]) * 25)),
        "documentation": min(100, max(0, (asset.lines_of_code / 1000) * 2 + 40)),
        "test_coverage": min(100, max(0, 50 + (asset.lines_of_code / 500))) if asset.lines_of_code else 30,
        "dependency_health": 85.0,
        "license_integrity": min(100, max(0, 100 - len([r for r in asset.risks if r.category == "license" and not r.is_resolved]) * 30)),
        "code_quality": 70.0,
        "security_posture": min(100, max(0, 100 - len([r for r in asset.risks if r.category == "security" and not r.is_resolved]) * 35)),
        "commercial_viability": min(100, max(0, asset.strategic_value / 1000)),
        "financial_traceability": 60.0,
        "market_comparables": 50.0,
    }
    deductions = []
    for r in asset.risks:
        if not r.is_resolved:
            d = {"reason": r.reason, "severity": r.severity, "points": {"low": 2, "medium": 5, "high": 10, "critical": 20}.get(r.severity, 5)}
            deductions.append(d)
    raw = sum(comps.values()) / len(comps)
    total_deduction = sum(d["points"] for d in deductions)
    score = max(0, raw - total_deduction)
    return {"score": round(score, 1), "components": comps, "deductions": deductions}


# ─── Asset Register CRUD ────────────────────────────────────────

@router.post("/assets", response_model=AssetOut)
def create_asset(body: AssetCreate):
    with get_session() as session:
        a = Asset(
            name=body.name,
            type=AssetType(body.type) if body.type else AssetType.REPO,
            status=AssetStatus(body.status) if body.status else AssetStatus.ACTIVE,
            strategic_value=body.strategic_value,
            buyer_today_value=body.buyer_today_value,
            liquidation_value=body.liquidation_value,
            collateral_support=body.collateral_support,
            financeability_score=body.financeability_score,
            risk_score=body.risk_score,
            lines_of_code=body.lines_of_code,
            tech_stack=body.tech_stack,
            repo_url=body.repo_url,
            owner=body.owner,
        )
        session.add(a)
        session.commit()
        session.refresh(a)
        _log(session, "CREATE", "Asset", a.id, {"name": a.name})
        return AssetOut.model_validate(a)


@router.get("/assets")
def list_assets(
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None),
    max_score: Optional[float] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("financeability_score"),
    order: str = Query("desc"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    with get_session() as session:
        q = session.query(Asset)
        if status:
            q = q.filter(Asset.status == status)
        if type:
            q = q.filter(Asset.type == type)
        if min_score is not None:
            q = q.filter(Asset.financeability_score >= min_score)
        if max_score is not None:
            q = q.filter(Asset.financeability_score <= max_score)
        if search:
            q = q.filter(Asset.name.ilike(f"%{search}%"))
        col = getattr(Asset, sort_by, Asset.financeability_score)
        if order.lower() == "desc":
            q = q.order_by(col.desc())
        else:
            q = q.order_by(col.asc())
        total = q.count()
        items = q.offset(offset).limit(limit).all()
        return {"total": total, "offset": offset, "limit": limit, "items": [_asset_to_dict(a) for a in items]}


@router.get("/assets/{asset_id}", response_model=AssetOut)
def get_asset(asset_id: str):
    with get_session() as session:
        a = session.query(Asset).filter(Asset.id == asset_id).first()
        if not a:
            raise HTTPException(status_code=404, detail="Asset not found")
        return AssetOut.model_validate(a)


@router.patch("/assets/{asset_id}", response_model=AssetOut)
def update_asset(asset_id: str, body: AssetUpdate):
    with get_session() as session:
        a = session.query(Asset).filter(Asset.id == asset_id).first()
        if not a:
            raise HTTPException(status_code=404, detail="Asset not found")
        for field, value in body.model_dump(exclude_unset=True).items():
            if field in ("type", "status") and value is not None:
                value = AssetType(value) if field == "type" else AssetStatus(value)
            setattr(a, field, value)
        a.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(a)
        _log(session, "UPDATE", "Asset", a.id, body.model_dump(exclude_unset=True))
        return AssetOut.model_validate(a)


@router.delete("/assets/{asset_id}")
def delete_asset(asset_id: str):
    with get_session() as session:
        a = session.query(Asset).filter(Asset.id == asset_id).first()
        if not a:
            raise HTTPException(status_code=404, detail="Asset not found")
        session.delete(a)
        session.commit()
        _log(session, "DELETE", "Asset", asset_id, {})
        return {"deleted": True}


# ─── Financeability ─────────────────────────────────────────────

@router.get("/assets/{asset_id}/financeability")
def get_financeability(asset_id: str):
    with get_session() as session:
        a = session.query(Asset).filter(Asset.id == asset_id).first()
        if not a:
            raise HTTPException(status_code=404, detail="Asset not found")
        result = _compute_financeability(a)
        a.financeability_score = result["score"]
        session.commit()
        return FinanceabilityResult(
            asset_id=a.id,
            asset_name=a.name,
            score=result["score"],
            components=result["components"],
            deductions=result["deductions"],
        )


@router.post("/assets/{asset_id}/financeability/recalculate")
def recalculate_financeability(asset_id: str):
    with get_session() as session:
        a = session.query(Asset).filter(Asset.id == asset_id).first()
        if not a:
            raise HTTPException(status_code=404, detail="Asset not found")
        result = _compute_financeability(a)
        a.financeability_score = result["score"]
        session.commit()
        return {"score": result["score"], "components": result["components"], "deductions": result["deductions"]}


# ─── Valuations ─────────────────────────────────────────────────

@router.post("/assets/{asset_id}/valuations")
def create_valuation(asset_id: str, body: ValuationCreate):
    with get_session() as session:
        a = session.query(Asset).filter(Asset.id == asset_id).first()
        if not a:
            raise HTTPException(status_code=404, detail="Asset not found")
        v = ValuationSet(asset_id=asset_id, method=body.method, value=body.value,
                         confidence=body.confidence, details=body.details)
        session.add(v)
        session.commit()
        session.refresh(v)
        _log(session, "CREATE", "ValuationSet", v.id, {"method": body.method, "value": body.value})
        return {"id": v.id, "asset_id": v.asset_id, "method": v.method, "value": v.value,
                "confidence": v.confidence, "details": v.details, "created_at": v.created_at.isoformat()}


@router.get("/assets/{asset_id}/valuations")
def list_valuations(asset_id: str):
    with get_session() as session:
        vals = session.query(ValuationSet).filter(ValuationSet.asset_id == asset_id).order_by(ValuationSet.created_at.desc()).all()
        return [{"id": v.id, "method": v.method, "value": v.value, "confidence": v.confidence,
                 "details": v.details, "created_at": v.created_at.isoformat()} for v in vals]


# ─── Evidence / Proof Chain ─────────────────────────────────────

@router.post("/assets/{asset_id}/proofs")
def create_proof(asset_id: str, body: ProofCreate):
    with get_session() as session:
        a = session.query(Asset).filter(Asset.id == asset_id).first()
        if not a:
            raise HTTPException(status_code=404, detail="Asset not found")
        last = session.query(ProofEvent).filter(ProofEvent.asset_id == asset_id).order_by(ProofEvent.created_at.desc()).first()
        prev = last.hash if last else "0" * 64
        payload = json.dumps(body.metadata, sort_keys=True, default=str)
        h = _hash(f"{asset_id}:{body.event_type}:{body.description}:{payload}:{prev}")
        p = ProofEvent(
            asset_id=asset_id,
            event_type=body.event_type,
            description=body.description,
            hash=h,
            prev_hash=prev,
            metadata=body.metadata,
        )
        session.add(p)
        session.commit()
        session.refresh(p)
        _log(session, "CREATE", "ProofEvent", p.id, {"event_type": body.event_type})
        return {"id": p.id, "hash": h, "prev_hash": prev, "created_at": p.created_at.isoformat()}


@router.get("/assets/{asset_id}/proofs")
def list_proofs(asset_id: str):
    with get_session() as session:
        proofs = session.query(ProofEvent).filter(ProofEvent.asset_id == asset_id).order_by(ProofEvent.created_at.asc()).all()
        return [{"id": p.id, "event_type": p.event_type, "description": p.description,
                 "hash": p.hash, "prev_hash": p.prev_hash, "metadata": p.metadata,
                 "created_at": p.created_at.isoformat()} for p in proofs]


@router.get("/assets/{asset_id}/proofs/verify")
def verify_proof_chain(asset_id: str):
    """Verify tamper-evident chain integrity."""
    with get_session() as session:
        proofs = session.query(ProofEvent).filter(ProofEvent.asset_id == asset_id).order_by(ProofEvent.created_at.asc()).all()
        if not proofs:
            return {"valid": True, "count": 0}
        prev = "0" * 64
        for p in proofs:
            payload = json.dumps(p.metadata, sort_keys=True, default=str)
            expected = _hash(f"{asset_id}:{p.event_type}:{p.description}:{payload}:{prev}")
            if p.hash != expected or p.prev_hash != prev:
                return {"valid": False, "broken_at": p.id, "expected": expected, "got": p.hash}
            prev = p.hash
        return {"valid": True, "count": len(proofs), "latest_hash": prev}


# ─── Risk Flags ─────────────────────────────────────────────────

@router.post("/assets/{asset_id}/risks")
def create_risk(asset_id: str, body: RiskCreate):
    with get_session() as session:
        a = session.query(Asset).filter(Asset.id == asset_id).first()
        if not a:
            raise HTTPException(status_code=404, detail="Asset not found")
        r = RiskFlag(asset_id=asset_id, category=body.category, severity=body.severity,
                     reason=body.reason, remediation=body.remediation)
        session.add(r)
        session.commit()
        session.refresh(r)
        _log(session, "CREATE", "RiskFlag", r.id, {"category": body.category, "severity": body.severity})
        return {"id": r.id, "category": r.category, "severity": r.severity,
                "reason": r.reason, "is_resolved": r.is_resolved, "created_at": r.created_at.isoformat()}


@router.get("/assets/{asset_id}/risks")
def list_risks(asset_id: str, unresolved_only: bool = Query(False)):
    with get_session() as session:
        q = session.query(RiskFlag).filter(RiskFlag.asset_id == asset_id)
        if unresolved_only:
            q = q.filter(RiskFlag.is_resolved == False)
        risks = q.order_by(RiskFlag.created_at.desc()).all()
        return [{"id": r.id, "category": r.category, "severity": r.severity,
                 "reason": r.reason, "remediation": r.remediation,
                 "is_resolved": r.is_resolved, "created_at": r.created_at.isoformat()} for r in risks]


@router.patch("/assets/{asset_id}/risks/{risk_id}")
def update_risk(asset_id: str, risk_id: str, is_resolved: bool = Query(...)):
    with get_session() as session:
        r = session.query(RiskFlag).filter(RiskFlag.id == risk_id, RiskFlag.asset_id == asset_id).first()
        if not r:
            raise HTTPException(status_code=404, detail="Risk not found")
        r.is_resolved = is_resolved
        if is_resolved:
            r.resolved_at = datetime.utcnow()
        session.commit()
        _log(session, "UPDATE", "RiskFlag", r.id, {"is_resolved": is_resolved})
        return {"id": r.id, "is_resolved": r.is_resolved}


# ─── Collateral Packet Sections ─────────────────────────────────

@router.get("/assets/{asset_id}/packet")
def get_packet(asset_id: str):
    with get_session() as session:
        a = session.query(Asset).filter(Asset.id == asset_id).first()
        if not a:
            raise HTTPException(status_code=404, detail="Asset not found")
        sections = session.query(PacketSection).filter(PacketSection.asset_id == asset_id).all()
        total = len(sections)
        complete = sum(1 for s in sections if s.is_complete)
        return {
            "asset_id": asset_id,
            "asset_name": a.name,
            "readiness": round((complete / total * 100), 1) if total else 0.0,
            "total_sections": total,
            "complete_sections": complete,
            "sections": [{"id": s.id, "key": s.section_key, "title": s.title,
                          "is_complete": s.is_complete, "completeness": s.completeness,
                          "evidence_count": s.evidence_count, "last_updated": s.last_updated.isoformat()} for s in sections]
        }


@router.patch("/assets/{asset_id}/packet/sections/{section_id}")
def update_packet_section(asset_id: str, section_id: str, body: PacketSectionUpdate):
    with get_session() as session:
        s = session.query(PacketSection).filter(PacketSection.id == section_id, PacketSection.asset_id == asset_id).first()
        if not s:
            raise HTTPException(status_code=404, detail="Section not found")
        if body.is_complete is not None:
            s.is_complete = body.is_complete
        if body.completeness is not None:
            s.completeness = body.completeness
        if body.evidence_count is not None:
            s.evidence_count = body.evidence_count
        s.last_updated = datetime.utcnow()
        session.commit()
        _log(session, "UPDATE", "PacketSection", s.id, body.model_dump(exclude_unset=True))
        return {"id": s.id, "is_complete": s.is_complete, "completeness": s.completeness}


# ─── Buyer Universe ─────────────────────────────────────────────

@router.post("/assets/{asset_id}/buyers")
def create_buyer(asset_id: str, body: BuyerCreate):
    with get_session() as session:
        a = session.query(Asset).filter(Asset.id == asset_id).first()
        if not a:
            raise HTTPException(status_code=404, detail="Asset not found")
        b = BuyerTarget(asset_id=asset_id, name=body.name, category=body.category,
                        probability=body.probability, estimated_recovery=body.estimated_recovery,
                        rationale=body.rationale)
        session.add(b)
        session.commit()
        session.refresh(b)
        return {"id": b.id, "name": b.name, "category": b.category, "probability": b.probability,
                "estimated_recovery": b.estimated_recovery, "contact_status": b.contact_status}


@router.get("/assets/{asset_id}/buyers")
def list_buyers(asset_id: str):
    with get_session() as session:
        buyers = session.query(BuyerTarget).filter(BuyerTarget.asset_id == asset_id).order_by(BuyerTarget.probability.desc()).all()
        return [{"id": b.id, "name": b.name, "category": b.category, "probability": b.probability,
                 "estimated_recovery": b.estimated_recovery, "contact_status": b.contact_status} for b in buyers]


# ─── Agent Work ───────────────────────────────────────────────────

@router.post("/assets/{asset_id}/agent-work")
def create_agent_work(asset_id: str, body: AgentWorkCreate):
    with get_session() as session:
        a = session.query(Asset).filter(Asset.id == asset_id).first()
        if not a:
            raise HTTPException(status_code=404, detail="Asset not found")
        w = AgentWorkRecord(asset_id=asset_id, agent_name=body.agent_name, action=body.action,
                            files_created=body.files_created, files_modified=body.files_modified,
                            tests_added=body.tests_added, docs_added=body.docs_added,
                            lines_added=body.lines_added, lines_deleted=body.lines_deleted,
                            build_status=body.build_status, duration_minutes=body.duration_minutes)
        session.add(w)
        session.commit()
        session.refresh(w)
        return {"id": w.id, "agent_name": w.agent_name, "action": w.action,
                "files_created": w.files_created, "files_modified": w.files_modified,
                "tests_added": w.tests_added, "docs_added": w.docs_added,
                "lines_added": w.lines_added, "lines_deleted": w.lines_deleted,
                "build_status": w.build_status, "duration_minutes": w.duration_minutes,
                "created_at": w.created_at.isoformat()}


@router.get("/assets/{asset_id}/agent-work")
def list_agent_work(asset_id: str):
    with get_session() as session:
        records = session.query(AgentWorkRecord).filter(AgentWorkRecord.asset_id == asset_id).order_by(AgentWorkRecord.created_at.desc()).all()
        return [{"id": w.id, "agent_name": w.agent_name, "action": w.action,
                 "files_created": w.files_created, "files_modified": w.files_modified,
                 "tests_added": w.tests_added, "docs_added": w.docs_added,
                 "lines_added": w.lines_added, "lines_deleted": w.lines_deleted,
                 "build_status": w.build_status, "duration_minutes": w.duration_minutes,
                 "created_at": w.created_at.isoformat()} for w in records]


# ─── Improvement Queue ──────────────────────────────────────────

@router.post("/assets/{asset_id}/improvements")
def create_improvement(asset_id: str, body: ImprovementCreate):
    with get_session() as session:
        a = session.query(Asset).filter(Asset.id == asset_id).first()
        if not a:
            raise HTTPException(status_code=404, detail="Asset not found")
        t = ImprovementTask(asset_id=asset_id, title=body.title, category=body.category,
                            impact_estimate=body.impact_estimate, effort_estimate=body.effort_estimate,
                            priority=body.priority)
        session.add(t)
        session.commit()
        session.refresh(t)
        return {"id": t.id, "title": t.title, "category": t.category,
                "impact_estimate": t.impact_estimate, "effort_estimate": t.effort_estimate,
                "priority": t.priority, "is_completed": t.is_completed}


@router.get("/assets/{asset_id}/improvements")
def list_improvements(asset_id: str, pending_only: bool = Query(False)):
    with get_session() as session:
        q = session.query(ImprovementTask).filter(ImprovementTask.asset_id == asset_id)
        if pending_only:
            q = q.filter(ImprovementTask.is_completed == False)
        tasks = q.order_by(ImprovementTask.priority.desc(), ImprovementTask.impact_estimate.desc()).all()
        return [{"id": t.id, "title": t.title, "category": t.category,
                 "impact_estimate": t.impact_estimate, "effort_estimate": t.effort_estimate,
                 "priority": t.priority, "is_completed": t.is_completed} for t in tasks]


@router.patch("/assets/{asset_id}/improvements/{task_id}")
def update_improvement(asset_id: str, task_id: str, is_completed: bool = Query(...)):
    with get_session() as session:
        t = session.query(ImprovementTask).filter(ImprovementTask.id == task_id, ImprovementTask.asset_id == asset_id).first()
        if not t:
            raise HTTPException(status_code=404, detail="Task not found")
        t.is_completed = is_completed
        if is_completed:
            t.completed_at = datetime.utcnow()
        session.commit()
        return {"id": t.id, "is_completed": t.is_completed}


# ─── Portfolio Summary ──────────────────────────────────────────

@router.get("/portfolio/summary")
def portfolio_summary():
    with get_session() as session:
        assets = session.query(Asset).all()
        total = len(assets)
        active = sum(1 for a in assets if a.status == AssetStatus.ACTIVE)
        risk_blocked = sum(1 for a in assets if a.status == AssetStatus.RISK_BLOCKED)
        strategic = sum(a.strategic_value for a in assets)
        buyer = sum(a.buyer_today_value for a in assets)
        liquidation = sum(a.liquidation_value for a in assets)
        collateral = sum(a.collateral_support for a in assets)
        avg_score = sum(a.financeability_score for a in assets) / total if total else 0
        return {
            "total_assets": total,
            "active": active,
            "risk_blocked": risk_blocked,
            "strategic_value": round(strategic, 2),
            "buyer_today_value": round(buyer, 2),
            "liquidation_value": round(liquidation, 2),
            "collateral_support": round(collateral, 2),
            "avg_financeability": round(avg_score, 1),
        }


# ─── CSV Import / Export ────────────────────────────────────────

@router.post("/import/csv")
def import_csv(file: UploadFile = File(...)):
    contents = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(contents))
    imported = 0
    with get_session() as session:
        for row in reader:
            tech = row.get("tech_stack", "").split("|") if row.get("tech_stack") else []
            a = Asset(
                name=row.get("name", "Unnamed"),
                type=AssetType(row.get("type", "repo")),
                status=AssetStatus(row.get("status", "active")),
                strategic_value=float(row.get("strategic_value", 0) or 0),
                buyer_today_value=float(row.get("buyer_today_value", 0) or 0),
                liquidation_value=float(row.get("liquidation_value", 0) or 0),
                collateral_support=float(row.get("collateral_support", 0) or 0),
                lines_of_code=int(row.get("lines_of_code", 0) or 0),
                repo_url=row.get("repo_url") or None,
                owner=row.get("owner") or None,
                tech_stack=tech,
            )
            session.add(a)
            imported += 1
        session.commit()
    return {"imported": imported}


@router.get("/export/csv")
def export_csv():
    with get_session() as session:
        assets = session.query(Asset).order_by(Asset.name).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "name", "type", "status", "strategic_value", "buyer_today_value",
                         "liquidation_value", "collateral_support", "financeability_score",
                         "risk_score", "lines_of_code", "repo_url", "owner", "tech_stack", "created_at"])
        for a in assets:
            writer.writerow([a.id, a.name, a.type.value, a.status.value, a.strategic_value,
                             a.buyer_today_value, a.liquidation_value, a.collateral_support,
                             a.financeability_score, a.risk_score, a.lines_of_code,
                             a.repo_url or "", a.owner or "", "|".join(a.tech_stack or []),
                             a.created_at.isoformat()])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=collateralops_assets.csv"})


@router.get("/export/json")
def export_json():
    with get_session() as session:
        assets = session.query(Asset).order_by(Asset.name).all()
        data = []
        for a in assets:
            data.append({
                "asset": _asset_to_dict(a),
                "valuations": [{"method": v.method, "value": v.value, "confidence": v.confidence} for v in a.valuations],
                "risks": [{"category": r.category, "severity": r.severity, "reason": r.reason, "is_resolved": r.is_resolved} for r in a.risks],
                "improvements": [{"title": t.title, "category": t.category, "impact": t.impact_estimate, "completed": t.is_completed} for t in a.improvements],
            })
    return JSONResponse(content={"generated_at": datetime.utcnow().isoformat(), "assets": data})

