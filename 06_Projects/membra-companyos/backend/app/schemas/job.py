"""JobOS schemas — Job, Bounty, WorkOrder, MarketplaceAction, JobProof."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class JobCreate(BaseModel):
    task_id: Optional[str] = None
    company_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    job_type: str
    budget: Optional[float] = None
    currency: Optional[str] = "USD"
    assigned_to: Optional[str] = None
    assigned_agent_id: Optional[str] = None
    asset_id: Optional[str] = None
    location_json: Optional[Dict[str, Any]] = {}
    requirements: Optional[List[str]] = []
    deliverables: Optional[List[str]] = []
    deadline: Optional[datetime] = None
    metadata_json: Optional[Dict[str, Any]] = {}


class JobRead(BaseModel):
    id: str
    task_id: Optional[str] = None
    company_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    job_type: str
    status: str
    budget: Optional[float] = None
    currency: str
    payout_eligible: bool
    payout_amount: float
    assigned_to: Optional[str] = None
    assigned_agent_id: Optional[str] = None
    asset_id: Optional[str] = None
    deadline: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = None
    assigned_to: Optional[str] = None
    assigned_agent_id: Optional[str] = None
    deadline: Optional[datetime] = None
    metadata_json: Optional[Dict[str, Any]] = None


class BountyCreate(BaseModel):
    job_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    reward_amount: float
    currency: Optional[str] = "USD"
    requirements: Optional[List[str]] = []
    deadline: Optional[datetime] = None


class WorkOrderCreate(BaseModel):
    job_id: Optional[str] = None
    wo_number: str
    title: str
    crew_assignment: Optional[List[Dict[str, Any]]] = []
    schedule_json: Optional[Dict[str, Any]] = {}
    equipment_json: Optional[List[str]] = []
    cost_estimate: Optional[float] = None


class MarketplaceActionCreate(BaseModel):
    job_id: Optional[str] = None
    action_type: str
    asset_type: str
    asset_id: Optional[str] = None
    listing_price: Optional[float] = None
    visibility: Optional[str] = "private"


class JobProofCreate(BaseModel):
    job_id: str
    proof_type: str
    proof_data: Optional[Dict[str, Any]] = {}
    ipfs_cid: Optional[str] = None
    proof_hash: str
