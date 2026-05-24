"""MEMBRA CompanyOS — TaskOS service."""
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus, TaskType, TaskDependency, TaskAssignment, TaskProof
from app.schemas.task import TaskCreate, TaskUpdate, TaskDependencyCreate, TaskAssignmentCreate, TaskProofCreate
from app.core.logging import get_logger
from app.services.proofbook import ProofBookService

logger = get_logger(__name__)


class TaskService:
    def __init__(self, db: Session):
        self.db = db
        self.proof = ProofBookService(db)

    def create_task(self, data: TaskCreate) -> Task:
        task = Task(
            objective_id=UUID(data.objective_id) if data.objective_id else None,
            company_id=UUID(data.company_id) if data.company_id else None,
            title=data.title,
            description=data.description,
            task_type=TaskType(data.task_type),
            priority=data.priority,
            owner_id=UUID(data.owner_id) if data.owner_id else None,
            owner_agent_id=UUID(data.owner_agent_id) if data.owner_agent_id else None,
            estimated_hours=data.estimated_hours,
            deadline=data.deadline,
            proof_requirement=data.proof_requirement or {},
            output_schema=data.output_schema or {},
            metadata_json=data.metadata_json or {},
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        self.proof.write_entry(
            entry_type="TASK_CREATED",
            resource_type="task",
            resource_id=task.id,
            actor_type="system",
            actor_id=task.owner_id or UUID("00000000-0000-0000-0000-000000000000"),
            description=f"Task created: {data.title}",
            data={"task_type": data.task_type, "priority": data.priority},
        )
        return task

    def update_status(self, task_id: str, status: str, reason: Optional[str] = None) -> Task:
        task = self.db.query(Task).filter(Task.id == UUID(task_id)).first()
        if not task:
            raise ValueError("Task not found")
        old_status = task.status.value
        task.status = TaskStatus(status)
        if reason:
            task.blocked_reason = reason
        if status == "completed":
            self._check_dependents(task.id)
        self.db.commit()
        self.db.refresh(task)
        self.proof.write_entry(
            entry_type="TASK_COMPLETED" if status == "completed" else "TASK_UPDATED",
            resource_type="task",
            resource_id=task.id,
            actor_type="system",
            actor_id=task.owner_id or UUID("00000000-0000-0000-0000-000000000000"),
            description=f"Task {task_id} moved from {old_status} to {status}",
            data={"old_status": old_status, "new_status": status, "reason": reason},
        )
        return task

    def add_dependency(self, data: TaskDependencyCreate) -> TaskDependency:
        dep = TaskDependency(
            task_id=UUID(data.task_id),
            depends_on_task_id=UUID(data.depends_on_task_id),
            dependency_type=data.dependency_type,
        )
        self.db.add(dep)
        self.db.commit()
        self.db.refresh(dep)
        return dep

    def assign_task(self, data: TaskAssignmentCreate) -> TaskAssignment:
        assignment = TaskAssignment(
            task_id=UUID(data.task_id),
            assignee_type=data.assignee_type,
            assignee_id=UUID(data.assignee_id),
            notes=data.notes,
        )
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def submit_proof(self, data: TaskProofCreate) -> TaskProof:
        proof = TaskProof(
            task_id=UUID(data.task_id),
            proof_type=data.proof_type,
            proof_data=data.proof_data or {},
            ipfs_cid=data.ipfs_cid,
            proof_hash=data.proof_hash,
        )
        self.db.add(proof)
        self.db.commit()
        self.db.refresh(proof)
        self.proof.write_entry(
            entry_type="TASK_COMPLETED",
            resource_type="task_proof",
            resource_id=proof.id,
            actor_type="system",
            actor_id=UUID(data.task_id),
            description=f"Proof submitted for task {data.task_id}",
            data={"proof_type": data.proof_type, "hash": data.proof_hash},
        )
        return proof

    def list_tasks(self, company_id: Optional[str] = None, status: Optional[str] = None, limit: int = 50) -> List[Task]:
        q = self.db.query(Task)
        if company_id:
            q = q.filter(Task.company_id == UUID(company_id))
        if status:
            q = q.filter(Task.status == TaskStatus(status))
        return q.order_by(Task.created_at.desc()).limit(limit).all()

    def _check_dependents(self, completed_task_id: UUID):
        deps = self.db.query(TaskDependency).filter(TaskDependency.depends_on_task_id == completed_task_id).all()
        for dep in deps:
            task = self.db.query(Task).filter(Task.id == dep.task_id).first()
            if task and task.status == TaskStatus.BLOCKED:
                all_cleared = all(
                    d.task.status == TaskStatus.COMPLETED
                    for d in self.db.query(TaskDependency).filter(TaskDependency.task_id == task.id).all()
                    if d.task
                )
                if all_cleared:
                    task.status = TaskStatus.BACKLOG
                    task.blocked_reason = None
        self.db.commit()
