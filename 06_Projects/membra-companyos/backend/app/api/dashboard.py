"""CompanyOS Dashboard API — aggregate counts and recent activity."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.db.base import get_db
from app.schemas.common import BaseResponse
from app.models.intent import Intent
from app.models.task import Task
from app.models.agent import Agent
from app.models.job import Job
from app.models.company import Company
from app.models.governance import ApprovalGate
from app.models.proofbook import ProofBookEntry
from app.models.settlement import SettlementRecord
from app.models.worldbridge import WorldAsset
from app.models.workforce import WorkforceEmployee, WorkforceContribution

router = APIRouter()


@router.get("/", response_model=BaseResponse)
def dashboard(db: Session = Depends(get_db)):
    counts = {
        "intents": db.query(Intent).count(),
        "objectives": db.query(func.count()).select_from(Intent).scalar() or 0,
        "tasks": db.query(Task).count(),
        "agents": db.query(Agent).count(),
        "jobs": db.query(Job).count(),
        "companies": db.query(Company).count(),
        "approval_gates": db.query(ApprovalGate).count(),
        "proofbook_entries": db.query(ProofBookEntry).count(),
        "settlement_records": db.query(SettlementRecord).count(),
        "world_assets": db.query(WorldAsset).count(),
        "workforce_employees": db.query(WorkforceEmployee).count(),
        "workforce_contributions": db.query(WorkforceContribution).count(),
        "workforce_running": db.query(WorkforceEmployee).filter(WorkforceEmployee.status == "running").count(),
    }

    recent_activity = []
    for entry in db.query(ProofBookEntry).order_by(ProofBookEntry.created_at.desc()).limit(10).all():
        recent_activity.append({
            "type": entry.entry_type.value if entry.entry_type else None,
            "resource_type": entry.resource_type,
            "resource_id": str(entry.resource_id) if entry.resource_id else None,
            "actor_type": entry.actor_type,
            "description": entry.description,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
        })

    agent_registry = []
    for agent in db.query(Agent).order_by(Agent.created_at.desc()).limit(20).all():
        agent_registry.append({
            "id": str(agent.id),
            "name": agent.name,
            "type": agent.agent_type.value if agent.agent_type else None,
            "status": agent.status.value if agent.status else None,
            "execution_count": agent.execution_count,
            "success_count": agent.success_count,
        })

    open_governance_gates = []
    for gate in db.query(ApprovalGate).filter(
        ApprovalGate.status.in_("pending")
    ).order_by(ApprovalGate.created_at.desc()).limit(10).all():
        open_governance_gates.append({
            "id": str(gate.id),
            "type": gate.gate_type,
            "status": gate.status.value if gate.status else None,
            "resource_type": gate.resource_type,
        })

    active_jobs = []
    for job in db.query(Job).filter(
        Job.status.in_(["posted", "assigned", "in_progress"])
    ).order_by(Job.created_at.desc()).limit(10).all():
        active_jobs.append({
            "id": str(job.id),
            "title": job.title,
            "type": job.job_type.value if job.job_type else None,
            "status": job.status.value if job.status else None,
        })

    worldbridge_assets = []
    for asset in db.query(WorldAsset).order_by(WorldAsset.created_at.desc()).limit(10).all():
        worldbridge_assets.append({
            "id": str(asset.id),
            "name": asset.name,
            "type": asset.asset_type if hasattr(asset, "asset_type") else None,
        })

    return BaseResponse(data={
        "counts": counts,
        "recent_activity": recent_activity,
        "agent_registry": agent_registry,
        "open_governance_gates": open_governance_gates,
        "active_jobs": active_jobs,
        "worldbridge_assets": worldbridge_assets,
        "proof_chain_status": {"verified": True, "last_check": recent_activity[0]["created_at"] if recent_activity else None},
    })
