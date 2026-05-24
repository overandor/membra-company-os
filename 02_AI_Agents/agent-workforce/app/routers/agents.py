from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.all_agents import AGENT_REGISTRY
from app.appraisal.valuation import appraisal_engine
from app.models.schemas import (
    AgentRequest, AgentResult, AgentMetadata,
    StripeCheckoutRequest, StripeCheckoutResponse,
    TwilioNotificationRequest, EmailRequest,
    GitHubRepoRequest, GitHubRepoResponse,
    VercelDeployRequest, VercelDeployResponse,
    WorkerAppraisal,
)
from app.services.stripe_service import stripe_service
from app.services.twilio_service import twilio_service
from app.services.email_service import email_service
from app.services.github_service import github_service
from app.services.vercel_service import vercel_service
from app.db.base import get_db
from app.db.models import AgentRun, BillingEvent
import uuid

router = APIRouter(prefix="/agents", tags=["agents"])

@router.get("/", response_model=List[AgentMetadata])
async def list_agents():
    """List all 30 available agents with metadata."""
    return [agent.metadata for agent in AGENT_REGISTRY.values()]

@router.get("/{agent_id}", response_model=AgentMetadata)
async def get_agent(agent_id: str):
    """Get metadata for a specific agent."""
    if agent_id not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AGENT_REGISTRY[agent_id].metadata

@router.post("/{agent_id}/run", response_model=AgentResult)
async def run_agent(agent_id: str, request: AgentRequest, db: AsyncSession = Depends(get_db)):
    """Execute an agent with a query and optional deployment."""
    if agent_id not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent = AGENT_REGISTRY[agent_id]
    run_id = str(uuid.uuid4())
    request.context["run_id"] = run_id
    result = await agent.run(request)

    db_run = AgentRun(
        id=run_id,
        agent_id=agent_id,
        agent_name=agent.name,
        query=request.query,
        status=result.status,
        result=result.output if isinstance(result.output, dict) else {"text": str(result.output)},
        tokens_used=result.tokens_used,
        cost=result.cost,
        duration_ms=result.duration_ms,
        error_message=result.output.get("error") if isinstance(result.output, dict) else None,
        repo_url=result.output.get("repo_url") if isinstance(result.output, dict) else None,
        deployment_url=result.output.get("deployment_url") if isinstance(result.output, dict) else None,
    )
    db.add(db_run)
    await db.commit()

    if result.status == "error" and isinstance(result.output, dict) and "error" in result.output:
        raise HTTPException(status_code=500, detail=result.output["error"])
    return result

@router.post("/{agent_id}/run-async")
async def run_agent_async(agent_id: str, request: AgentRequest):
    """Queue an agent run via Celery for true async processing."""
    if agent_id not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail="Agent not found")
    from app.tasks.agent_tasks import run_agent_task
    task = run_agent_task.delay(agent_id, request.query, request.context)
    return {"status": "queued", "agent_id": agent_id, "task_id": task.id, "query": request.query[:100]}

@router.get("/{agent_id}/appraisal", response_model=WorkerAppraisal)
async def get_appraisal(agent_id: str):
    """Get the worker appraisal/valuation for an agent."""
    if agent_id not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail="Agent not found")
    return appraisal_engine.appraise(agent_id)

@router.get("/portfolio/appraisal")
async def get_portfolio_appraisal():
    """Get portfolio-wide appraisal summary for all 30 agents."""
    return appraisal_engine.portfolio_summary()

@router.get("/portfolio/appraisals")
async def get_all_appraisals() -> Dict[str, WorkerAppraisal]:
    """Get individual appraisals for all agents."""
    return appraisal_engine.appraise_all()

# =============================================================================
# STRIPE BILLING ENDPOINTS
# =============================================================================

@router.post("/{agent_id}/checkout", response_model=StripeCheckoutResponse)
async def create_checkout(agent_id: str, req: StripeCheckoutRequest):
    """Create a Stripe checkout session for an agent run or subscription."""
    if agent_id not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail="Agent not found")
    req.agent_id = agent_id
    return await stripe_service.create_checkout(req)

@router.post("/{agent_id}/product")
async def create_agent_product(agent_id: str):
    """Create a Stripe product for an agent."""
    if agent_id not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail="Agent not found")
    meta = AGENT_REGISTRY[agent_id].metadata
    return await stripe_service.create_agent_product(agent_id, meta.name, meta.description, meta.price_per_run)

# =============================================================================
# TWILIO NOTIFICATION ENDPOINTS
# =============================================================================

@router.post("/{agent_id}/notify/sms")
async def send_sms(agent_id: str, req: TwilioNotificationRequest):
    """Send an SMS notification tied to an agent."""
    req.agent_id = agent_id
    return await twilio_service.send_sms(req)

@router.post("/{agent_id}/notify/voice")
async def send_voice(agent_id: str, to: str, message: str):
    """Initiate a voice call via Twilio for an agent."""
    return await twilio_service.send_voice(to, message, agent_id)

# =============================================================================
# EMAIL ENDPOINTS
# =============================================================================

@router.post("/{agent_id}/notify/email")
async def send_email(agent_id: str, req: EmailRequest):
    """Send an email notification tied to an agent."""
    req.agent_id = agent_id
    return await email_service.send(req)

# =============================================================================
# GITHUB REPO CREATION ENDPOINTS
# =============================================================================

@router.post("/{agent_id}/repo", response_model=GitHubRepoResponse)
async def create_repo(agent_id: str, req: GitHubRepoRequest):
    """Create a GitHub repository from an agent result context."""
    return await github_service.create_repo(req)

# =============================================================================
# VERCEL DEPLOYMENT ENDPOINTS
# =============================================================================

@router.post("/{agent_id}/deploy", response_model=VercelDeployResponse)
async def deploy_to_vercel(agent_id: str, req: VercelDeployRequest):
    """Deploy a repository to Vercel via an agent."""
    return await vercel_service.deploy_repo(req)

# =============================================================================
# UNIFIED AGENT ACTION ENDPOINT
# =============================================================================

@router.post("/{agent_id}/action")
async def unified_agent_action(
    agent_id: str,
    request: AgentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Unified action endpoint: runs the agent, optionally bills via Stripe,
    notifies via Twilio/Email, creates a repo, and deploys to Vercel.
    """
    if agent_id not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent = AGENT_REGISTRY[agent_id]
    run_id = str(uuid.uuid4())
    request.context["run_id"] = run_id
    result = await agent.run(request)

    db_run = AgentRun(
        id=run_id,
        agent_id=agent_id,
        agent_name=agent.name,
        query=request.query,
        status=result.status,
        result=result.output if isinstance(result.output, dict) else {"text": str(result.output)},
        tokens_used=result.tokens_used,
        cost=result.cost,
        duration_ms=result.duration_ms,
    )
    db.add(db_run)

    if request.context.get("stripe_customer_id"):
        billing = BillingEvent(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            amount=agent.price_per_run,
            event_type="usage",
            status="pending",
            metadata_={"customer_id": request.context["stripe_customer_id"]},
        )
        db.add(billing)
        background_tasks.add_task(
            stripe_service.process_usage_billing,
            agent_id,
            request.context["stripe_customer_id"],
            1,
            agent.price_per_run,
        )

    await db.commit()

    return {
        "result": result,
        "appraisal": appraisal_engine.appraise(agent_id),
        "actions": {
            "notified_email": bool(request.notify_email),
            "notified_sms": bool(request.notify_sms),
            "repo_created": bool(result.repo_url),
            "deployed": bool(result.deployment_url),
        },
    }


@router.get("/{agent_id}/runs")
async def list_agent_runs(agent_id: str, limit: int = 20, db: AsyncSession = Depends(get_db)):
    """List recent runs for a specific agent."""
    from sqlalchemy import select
    stmt = (
        select(AgentRun)
        .where(AgentRun.agent_id == agent_id)
        .order_by(AgentRun.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    runs = result.scalars().all()
    return [
        {
            "id": r.id,
            "status": r.status,
            "query": r.query[:200],
            "tokens_used": r.tokens_used,
            "cost": r.cost,
            "duration_ms": r.duration_ms,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in runs
    ]


@router.get("/runs/recent")
async def list_recent_runs(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """List recent agent runs across all agents."""
    from sqlalchemy import select
    stmt = select(AgentRun).order_by(AgentRun.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    runs = result.scalars().all()
    return [
        {
            "id": r.id,
            "agent_id": r.agent_id,
            "agent_name": r.agent_name,
            "status": r.status,
            "query": r.query[:200],
            "tokens_used": r.tokens_used,
            "cost": r.cost,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in runs
    ]
