"""MEMBRA CompanyOS — OrchestrationOS service.
Converts user intent → objectives → tasks → assignments → jobs → proof → governance → settlement.
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.intent import Intent, IntentStatus, Objective
from app.models.task import Task, TaskStatus, TaskType
from app.models.job import Job, JobType, JobStatus
from app.models.governance import ApprovalGate, ApprovalStatus, RiskLevel
from app.core.logging import get_logger
from app.services.intent import IntentService
from app.services.task import TaskService
from app.services.agent import AgentService
from app.services.job import JobService
from app.services.governance import GovernanceService
from app.services.proofbook import ProofBookService
from app.schemas.intent import IntentCreate
from app.schemas.task import TaskCreate, TaskAssignmentCreate
from app.schemas.job import JobCreate
from app.schemas.governance import ApprovalGateCreate

logger = get_logger(__name__)


class OrchestrationService:
    def __init__(self, db: Session):
        self.db = db
        self.intent_svc = IntentService(db)
        self.task_svc = TaskService(db)
        self.agent_svc = AgentService(db)
        self.job_svc = JobService(db)
        self.gov_svc = GovernanceService(db)
        self.proof = ProofBookService(db)

    def orchestrate(self, raw_intent: str, user_wallet: Optional[str] = None,
                    user_id: Optional[str] = None, company_id: Optional[str] = None) -> Dict[str, Any]:
        # Step 1: Capture intent
        intent = self.intent_svc.create_intent(
            IntentCreate(raw_text=raw_intent, user_wallet=user_wallet, user_id=user_id)
        )
        logger.info("intent_created", intent_id=str(intent.id))

        # Step 2: Parse intent into structured objectives (deterministic fallback)
        objectives_data = self._parse_intent_to_objectives(raw_intent)
        intent = self.intent_svc.parse_intent(str(intent.id), {"parsed": objectives_data})
        objectives = self.intent_svc.structure_objectives(str(intent.id), objectives_data)
        logger.info("objectives_created", count=len(objectives))

        # Step 3: Break objectives into tasks
        tasks = []
        for obj in objectives:
            obj_tasks = self._objective_to_tasks(obj, company_id)
            for t_data in obj_tasks:
                task = self.task_svc.create_task(TaskCreate(**t_data))
                tasks.append(task)
        logger.info("tasks_created", count=len(tasks))

        # Step 4: Assign tasks to agents / humans
        assignments = []
        for task in tasks:
            assignment = self._assign_task(task, company_id)
            if assignment:
                assignments.append(assignment)
        logger.info("tasks_assigned", count=len(assignments))

        # Step 5: Convert tasks to jobs where applicable
        jobs = []
        for task in tasks:
            if task.task_type in [TaskType.HUMAN_WORK, TaskType.ASSET_DEPLOYMENT, TaskType.SETTLEMENT_TRIGGER]:
                job_data = self._task_to_job(task, company_id)
                job = self.job_svc.create_job(JobCreate(**job_data))
                jobs.append(job)
        logger.info("jobs_created", count=len(jobs))

        # Step 6: Create governance gates for high-risk items
        gates = []
        for job in jobs:
            if job.job_type in [JobType.MARKETPLACE_LISTING, JobType.CAR_AD_TASK, JobType.WINDOW_AD_TASK]:
                gate = self.gov_svc.create_gate(
                    ApprovalGateCreate(
                        gate_type="owner_consent",
                        resource_type="job",
                        resource_id=str(job.id),
                        risk_level="medium",
                        required_approvals=1,
                    )
                )
                gates.append(gate)
        logger.info("gates_created", count=len(gates))

        # Step 7: Write orchestration proof
        proof = self.proof.write_entry(
            entry_type="TASK_CREATED",
            resource_type="orchestration",
            resource_id=intent.id,
            actor_type="system",
            actor_id=UUID(user_id) if user_id else UUID("00000000-0000-0000-0000-000000000000"),
            description=f"Orchestrated intent into {len(tasks)} tasks, {len(jobs)} jobs, {len(gates)} gates",
            data={"objectives": len(objectives), "tasks": len(tasks), "jobs": len(jobs), "gates": len(gates)},
        )

        return {
            "intent_id": str(intent.id),
            "objectives": [{"id": str(o.id), "title": o.title} for o in objectives],
            "tasks": [{"id": str(t.id), "title": t.title, "status": t.status.value} for t in tasks],
            "jobs": [{"id": str(j.id), "title": j.title, "type": j.job_type.value} for j in jobs],
            "gates": [{"id": str(g.id), "type": g.gate_type, "status": g.status.value} for g in gates],
            "proof_hash": proof.proof_hash,
        }

    def _parse_intent_to_objectives(self, raw_intent: str) -> List[Dict[str, Any]]:
        raw = raw_intent.lower()
        objectives = []
        if any(w in raw for w in ["window", "car", "apartment", "wearable", "tool", "vehicle"]):
            objectives.append({
                "title": "Register and deploy real-world assets",
                "description": "Capture user's physical assets into WorldBridge",
                "assigned_department": "operations",
                "success_criteria": ["Assets registered", "Proof of ownership captured"],
            })
        if any(w in raw for w in ["ad", "advertise", "rent", "listing", "sell", "marketplace"]):
            objectives.append({
                "title": "Create marketplace listings and ad inventory",
                "description": "Convert assets into visible marketplace SKUs",
                "assigned_department": "sales",
                "success_criteria": ["Listings created", "Owner consent obtained"],
            })
        if any(w in raw for w in ["task", "work", "job", "bounty", "help", "delivery"]):
            objectives.append({
                "title": "Create local work opportunities",
                "description": "Turn capacity into assignable jobs and bounties",
                "assigned_department": "operations",
                "success_criteria": ["Jobs posted", "Assignees matched"],
            })
        if any(w in raw for w in ["kpi", "dashboard", "track", "analytics", "measure"]):
            objectives.append({
                "title": "Establish KPI tracking and company memory",
                "description": "Create metrics for the new operating unit",
                "assigned_department": "finance",
                "success_criteria": ["KPIs defined", "Dashboard configured"],
            })
        if not objectives:
            objectives.append({
                "title": "Analyze and structure user intent",
                "description": raw_intent[:200],
                "assigned_department": "strategy",
                "success_criteria": ["Intent parsed", "Next steps defined"],
            })
        return objectives

    def _objective_to_tasks(self, obj: Objective, company_id: Optional[str]) -> List[Dict[str, Any]]:
        tasks = []
        if "Register and deploy" in obj.title:
            tasks.append({
                "objective_id": str(obj.id),
                "company_id": company_id,
                "title": "Inventory physical assets",
                "task_type": "proof_collection",
                "priority": 1,
                "proof_requirement": {"type": "photos", "min_count": 1},
            })
            tasks.append({
                "objective_id": str(obj.id),
                "company_id": company_id,
                "title": "Register assets in WorldBridge",
                "task_type": "asset_deployment",
                "priority": 2,
                "proof_requirement": {"type": "blockchain_tx", "required": False},
            })
        elif "marketplace listings" in obj.title:
            tasks.append({
                "objective_id": str(obj.id),
                "company_id": company_id,
                "title": "Draft marketplace listings",
                "task_type": "ai_analysis",
                "priority": 1,
                "output_schema": {"title": "string", "price": "number", "description": "string"},
            })
            tasks.append({
                "objective_id": str(obj.id),
                "company_id": company_id,
                "title": "Obtain owner consent for visibility",
                "task_type": "governance_gate",
                "priority": 2,
                "proof_requirement": {"type": "signature", "required": True},
            })
        elif "local work opportunities" in obj.title:
            tasks.append({
                "objective_id": str(obj.id),
                "company_id": company_id,
                "title": "Define job requirements and budget",
                "task_type": "ai_analysis",
                "priority": 1,
            })
            tasks.append({
                "objective_id": str(obj.id),
                "company_id": company_id,
                "title": "Post jobs to local marketplace",
                "task_type": "human_work",
                "priority": 2,
            })
        else:
            tasks.append({
                "objective_id": str(obj.id),
                "company_id": company_id,
                "title": f"Analyze: {obj.title}",
                "task_type": "ai_analysis",
                "priority": 3,
            })
        return tasks

    def _assign_task(self, task: Task, company_id: Optional[str]) -> Optional[Dict[str, Any]]:
        # Simple rule-based assignment
        if task.task_type == TaskType.AI_ANALYSIS:
            agents = self.agent_svc.list_agents(company_id=company_id, agent_type="strategy", limit=1)
            if agents:
                return self.task_svc.assign_task(
                    TaskAssignmentCreate(
                        task_id=str(task.id),
                        assignee_type="agent",
                        assignee_id=str(agents[0].id),
                    )
                )
        elif task.task_type == TaskType.HUMAN_WORK:
            # Would match to available people
            pass
        elif task.task_type == TaskType.GOVERNANCE_GATE:
            return self.task_svc.assign_task(
                TaskAssignmentCreate(
                    task_id=str(task.id),
                    assignee_type="human",
                    assignee_id=str(UUID("00000000-0000-0000-0000-000000000000")),
                )
            )
        return None

    def _task_to_job(self, task: Task, company_id: Optional[str]) -> Dict[str, Any]:
        job_type_map = {
            TaskType.HUMAN_WORK.value: JobType.BOUNTY.value,
            TaskType.ASSET_DEPLOYMENT.value: JobType.FULFILLMENT.value,
            TaskType.SETTLEMENT_TRIGGER.value: JobType.ADMIN_REVIEW.value,
        }
        return {
            "task_id": str(task.id),
            "company_id": company_id,
            "title": task.title,
            "description": task.description,
            "job_type": job_type_map.get(task.task_type.value, JobType.BOUNTY.value),
        }
