"""MEMBRA CompanyOS — AgentOS service."""
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.agent import Agent, AgentType, AgentStatus, AgentTool, AgentActionLog
from app.schemas.agent import AgentCreate, AgentUpdate, AgentToolCreate
from app.core.logging import get_logger
from app.services.proofbook import ProofBookService

logger = get_logger(__name__)


class AgentService:
    def __init__(self, db: Session):
        self.db = db
        self.proof = ProofBookService(db)

    def register_agent(self, data: AgentCreate) -> Agent:
        agent = Agent(
            agent_type=AgentType(data.agent_type),
            name=data.name,
            description=data.description,
            llm_provider=data.llm_provider,
            llm_model=data.llm_model,
            system_prompt=data.system_prompt,
            allowed_actions=data.allowed_actions or [],
            blocked_actions=data.blocked_actions or [],
            output_schema=data.output_schema or {},
            permissions=data.permissions or [],
            company_id=UUID(data.company_id) if data.company_id else None,
            department_id=UUID(data.department_id) if data.department_id else None,
            owner_wallet=data.owner_wallet,
            metadata_json=data.metadata_json or {},
        )
        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        self.proof.write_entry(
            entry_type="TASK_CREATED",
            resource_type="agent",
            resource_id=agent.id,
            actor_type="system",
            actor_id=UUID("00000000-0000-0000-0000-000000000000"),
            description=f"Agent registered: {data.name} ({data.agent_type})",
            data={"agent_type": data.agent_type, "permissions": data.permissions},
        )
        return agent

    def update_agent(self, agent_id: str, data: AgentUpdate) -> Agent:
        agent = self.db.query(Agent).filter(Agent.id == UUID(agent_id)).first()
        if not agent:
            raise ValueError("Agent not found")
        for field, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(agent, field, value)
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def add_tool(self, data: AgentToolCreate) -> AgentTool:
        tool = AgentTool(
            agent_id=UUID(data.agent_id),
            tool_name=data.tool_name,
            tool_description=data.tool_description,
            tool_schema=data.tool_schema or {},
            requires_human_approval=data.requires_human_approval,
            rate_limit_per_minute=data.rate_limit_per_minute,
        )
        self.db.add(tool)
        self.db.commit()
        self.db.refresh(tool)
        return tool

    def log_action(self, agent_id: str, action_type: str, task_id: Optional[str] = None,
                   job_id: Optional[str] = None, input_data: Optional[dict] = None,
                   output_data: Optional[dict] = None, status: str = "success",
                   error: Optional[str] = None, execution_time_ms: Optional[int] = None,
                   governance_passed: bool = True) -> AgentActionLog:
        log = AgentActionLog(
            agent_id=UUID(agent_id),
            action_type=action_type,
            task_id=UUID(task_id) if task_id else None,
            job_id=UUID(job_id) if job_id else None,
            input_data=input_data or {},
            output_data=output_data or {},
            status=status,
            error_message=error,
            execution_time_ms=execution_time_ms,
            governance_gate_passed=governance_passed,
        )
        self.db.add(log)
        agent = self.db.query(Agent).filter(Agent.id == UUID(agent_id)).first()
        if agent:
            agent.execution_count += 1
            if status == "success":
                agent.success_count += 1
        self.db.commit()
        self.db.refresh(log)
        self.proof.write_entry(
            entry_type="AGENT_ACTION",
            resource_type="agent_action",
            resource_id=log.id,
            actor_type="agent",
            actor_id=UUID(agent_id),
            description=f"Agent {agent_id} executed {action_type}: {status}",
            data={"action_type": action_type, "status": status, "governance_passed": governance_passed},
        )
        return log

    def list_agents(self, company_id: Optional[str] = None, agent_type: Optional[str] = None, limit: int = 50) -> List[Agent]:
        q = self.db.query(Agent)
        if company_id:
            q = q.filter(Agent.company_id == UUID(company_id))
        if agent_type:
            q = q.filter(Agent.agent_type == AgentType(agent_type))
        return q.order_by(Agent.created_at.desc()).limit(limit).all()
