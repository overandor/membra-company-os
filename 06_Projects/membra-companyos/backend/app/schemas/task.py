"""TaskOS schemas — Task, Dependency, Assignment, Proof."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class TaskCreate(BaseModel):
    objective_id: Optional[str] = None
    company_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    task_type: str
    priority: Optional[int] = 3
    owner_id: Optional[str] = None
    owner_agent_id: Optional[str] = None
    estimated_hours: Optional[str] = None
    deadline: Optional[datetime] = None
    proof_requirement: Optional[Dict[str, Any]] = {}
    output_schema: Optional[Dict[str, Any]] = {}
    metadata_json: Optional[Dict[str, Any]] = {}


class TaskRead(BaseModel):
    id: str
    objective_id: Optional[str] = None
    company_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    task_type: str
    status: str
    priority: int
    owner_id: Optional[str] = None
    owner_agent_id: Optional[str] = None
    estimated_hours: Optional[str] = None
    deadline: Optional[datetime] = None
    blocked_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    owner_id: Optional[str] = None
    owner_agent_id: Optional[str] = None
    deadline: Optional[datetime] = None
    blocked_reason: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class TaskDependencyCreate(BaseModel):
    task_id: str
    depends_on_task_id: str
    dependency_type: Optional[str] = "blocks"


class TaskAssignmentCreate(BaseModel):
    task_id: str
    assignee_type: str
    assignee_id: str
    notes: Optional[str] = None


class TaskProofCreate(BaseModel):
    task_id: str
    proof_type: str
    proof_data: Optional[Dict[str, Any]] = {}
    ipfs_cid: Optional[str] = None
    proof_hash: str
