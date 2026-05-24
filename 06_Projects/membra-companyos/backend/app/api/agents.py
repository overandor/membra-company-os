"""AgentOS API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.base import get_db
from app.services.agent import AgentService
from app.schemas.agent import AgentCreate, AgentRead, AgentUpdate, AgentToolCreate, AgentActionLogRead
from app.schemas.common import BaseResponse, PaginatedResponse

router = APIRouter()


@router.post("/", response_model=BaseResponse)
def register_agent(data: AgentCreate, db: Session = Depends(get_db)):
    svc = AgentService(db)
    agent = svc.register_agent(data)
    return BaseResponse(data={"id": str(agent.id), "status": agent.status.value})


@router.get("/", response_model=PaginatedResponse)
def list_agents(
    company_id: Optional[str] = None,
    agent_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    svc = AgentService(db)
    items = svc.list_agents(company_id=company_id, agent_type=agent_type, limit=limit)
    return PaginatedResponse(
        items=[AgentRead.model_validate(a) for a in items],
        total=len(items),
        page=1,
        page_size=limit,
        pages=1,
    )


@router.get("/{agent_id}", response_model=BaseResponse)
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    from uuid import UUID as PyUUID
    from app.models.agent import Agent
    agent = db.query(Agent).filter(Agent.id == PyUUID(agent_id)).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return BaseResponse(data={
        "id": str(agent.id),
        "name": agent.name,
        "type": agent.agent_type.value,
        "status": agent.status.value,
        "description": agent.description,
        "llm_provider": agent.llm_provider,
        "llm_model": agent.llm_model,
        "allowed_actions": agent.allowed_actions,
        "blocked_actions": agent.blocked_actions,
        "output_schema": agent.output_schema,
        "permissions": agent.permissions,
        "execution_count": agent.execution_count,
        "success_count": agent.success_count,
        "created_at": agent.created_at.isoformat() if agent.created_at else None,
    })


@router.patch("/{agent_id}", response_model=BaseResponse)
def update_agent(agent_id: str, data: AgentUpdate, db: Session = Depends(get_db)):
    svc = AgentService(db)
    agent = svc.update_agent(agent_id, data)
    return BaseResponse(data={"id": str(agent.id), "status": agent.status.value})


@router.post("/{agent_id}/tools", response_model=BaseResponse)
def add_tool(agent_id: str, data: AgentToolCreate, db: Session = Depends(get_db)):
    svc = AgentService(db)
    data.agent_id = agent_id
    tool = svc.add_tool(data)
    return BaseResponse(data={"id": str(tool.id), "name": tool.tool_name})


@router.post("/{agent_id}/actions", response_model=BaseResponse)
def log_action(
    agent_id: str,
    action_type: str,
    task_id: Optional[str] = None,
    job_id: Optional[str] = None,
    input_data: Optional[dict] = None,
    output_data: Optional[dict] = None,
    status: str = "success",
    error: Optional[str] = None,
    execution_time_ms: Optional[int] = None,
    governance_passed: bool = True,
    db: Session = Depends(get_db),
):
    svc = AgentService(db)
    log = svc.log_action(
        agent_id, action_type, task_id, job_id,
        input_data, output_data, status, error,
        execution_time_ms, governance_passed,
    )
    return BaseResponse(data={"id": str(log.id), "status": log.status})


@router.get("/{agent_id}/actions", response_model=PaginatedResponse)
def list_actions(
    agent_id: str,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    from uuid import UUID as PyUUID
    from app.models.agent import AgentActionLog
    logs = db.query(AgentActionLog).filter(
        AgentActionLog.agent_id == PyUUID(agent_id)
    ).order_by(AgentActionLog.created_at.desc()).limit(limit).all()
    return PaginatedResponse(
        items=[{
            "id": str(log.id),
            "action_type": log.action_type,
            "status": log.status,
            "task_id": str(log.task_id) if log.task_id else None,
            "job_id": str(log.job_id) if log.job_id else None,
            "execution_time_ms": log.execution_time_ms,
            "governance_gate_passed": log.governance_gate_passed,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        } for log in logs],
        total=len(logs),
        page=1,
        page_size=limit,
        pages=1,
    )


_DEFAULT_AGENTS = [
    {"name": "Strategy Agent", "type": "strategy", "purpose": "Decides what to build next", "allowed_tools": ["market_research", "competitor_analysis", "roadmap_planner"], "blocked_actions": ["settle_funds", "delete_company"], "permission_scope": "read_strategy", "output_schema": {"recommendation": "string", "confidence": "number", "next_steps": "list"}, "risk_level": "low", "requires_governance_gate": False},
    {"name": "Product Agent", "type": "product", "purpose": "Converts strategy into requirements", "allowed_tools": ["spec_writer", "user_story_generator", "prototype_reviewer"], "blocked_actions": ["deploy_production", "access_settlement"], "permission_scope": "read_product", "output_schema": {"specs": "list", "priority": "string"}, "risk_level": "low", "requires_governance_gate": False},
    {"name": "Engineering Agent", "type": "engineering", "purpose": "Builds and deploys", "allowed_tools": ["code_generator", "test_runner", "deploy_pipeline"], "blocked_actions": ["delete_database", "access_private_keys"], "permission_scope": "write_code", "output_schema": {"code": "string", "tests": "list", "deploy_ready": "boolean"}, "risk_level": "medium", "requires_governance_gate": True},
    {"name": "Ops Agent", "type": "operations", "purpose": "Creates SOPs and flows", "allowed_tools": ["sop_writer", "schedule_optimizer", "inventory_tracker"], "blocked_actions": ["modify_policies", "settle_funds"], "permission_scope": "read_operations", "output_schema": {"sop": "string", "schedule": "dict"}, "risk_level": "low", "requires_governance_gate": False},
    {"name": "Sales Agent", "type": "sales", "purpose": "Generates offers and outreach", "allowed_tools": ["offer_generator", "outreach_drafter", "crm_updater"], "blocked_actions": ["modify_contracts", "settle_funds"], "permission_scope": "write_offers", "output_schema": {"offer": "string", "target": "string"}, "risk_level": "medium", "requires_governance_gate": True},
    {"name": "Finance Agent", "type": "finance", "purpose": "Tracks unit economics", "allowed_tools": ["forecast_model", "report_generator", "kpi_tracker"], "blocked_actions": ["execute_transfers", "access_private_keys"], "permission_scope": "read_finance", "output_schema": {"forecast": "dict", "unit_economics": "dict"}, "risk_level": "medium", "requires_governance_gate": True},
    {"name": "Legal/Risk Agent", "type": "legal_risk", "purpose": "Flags risks and reviews compliance", "allowed_tools": ["policy_checker", "risk_scanner", "compliance_reviewer"], "blocked_actions": ["bypass_governance"], "permission_scope": "read_all", "output_schema": {"risk_level": "string", "flags": "list", "recommendation": "string"}, "risk_level": "high", "requires_governance_gate": True},
    {"name": "Governance Agent", "type": "governance", "purpose": "Controls approvals and escalation", "allowed_tools": ["gate_manager", "policy_enforcer", "escalation_router"], "blocked_actions": ["self_approve", "delete_audit_log"], "permission_scope": "admin_governance", "output_schema": {"decision": "string", "rationale": "string"}, "risk_level": "critical", "requires_governance_gate": True},
    {"name": "Proof Agent", "type": "proof", "purpose": "Writes to ProofBook and verifies chain", "allowed_tools": ["hash_generator", "chain_verifier", "ipfs_uploader"], "blocked_actions": ["delete_proof", "modify_hash"], "permission_scope": "write_proofbook", "output_schema": {"hash": "string", "verified": "boolean"}, "risk_level": "high", "requires_governance_gate": True},
    {"name": "Concierge Agent", "type": "concierge", "purpose": "Front-facing LLM that routes human intent", "allowed_tools": ["chat_handler", "intent_parser", "orchestration_router"], "blocked_actions": ["settle_funds", "delete_company", "bypass_governance"], "permission_scope": "read_concierge", "output_schema": {"reply": "string", "actions": "list", "orchestration": "dict"}, "risk_level": "low", "requires_governance_gate": False},
]


@router.get("/registry/defaults")
def get_default_agents():
    return BaseResponse(data=_DEFAULT_AGENTS)


@router.post("/registry/seed")
def seed_agent_registry(db: Session = Depends(get_db)):
    from app.models.agent import Agent, AgentType, AgentStatus
    created = 0
    skipped = 0
    for defn in _DEFAULT_AGENTS:
        exists = db.query(Agent).filter(Agent.name == defn["name"]).first()
        if exists:
            skipped += 1
            continue
        agent = Agent(
            agent_type=AgentType(defn["type"]),
            name=defn["name"],
            description=defn["purpose"],
            allowed_actions=defn["allowed_tools"],
            blocked_actions=defn["blocked_actions"],
            output_schema=defn["output_schema"],
            permissions=[defn["permission_scope"]],
            status=AgentStatus.ACTIVE,
        )
        db.add(agent)
        created += 1
    db.commit()
    return BaseResponse(data={"created": created, "skipped": skipped})
