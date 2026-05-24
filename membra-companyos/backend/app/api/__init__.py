from fastapi import APIRouter
from app.api import auth, intents, tasks, agents, jobs, companies, governance, proofbook, settlements, worldbridge, concierge, health, orchestrate, dashboard, workforce, agent_network

api_router = APIRouter(prefix="/v1")

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(intents.router, prefix="/intents", tags=["IntentOS"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["TaskOS"])
api_router.include_router(agents.router, prefix="/agents", tags=["AgentOS"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["JobOS"])
api_router.include_router(companies.router, prefix="/companies", tags=["CompanyOS"])
api_router.include_router(governance.router, prefix="/governance", tags=["GovernanceOS"])
api_router.include_router(proofbook.router, prefix="/proofbook", tags=["ProofBook"])
api_router.include_router(settlements.router, prefix="/settlements", tags=["SettlementOS"])
api_router.include_router(worldbridge.router, prefix="/worldbridge", tags=["WorldBridge"])
api_router.include_router(concierge.router, prefix="/concierge", tags=["LLM Concierge"])
api_router.include_router(orchestrate.router, prefix="/orchestrate", tags=["Orchestration"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(workforce.router, prefix="/workforce", tags=["Workforce"])
api_router.include_router(agent_network.router, prefix="/agent-network", tags=["Agent Network Protocol OS"])
