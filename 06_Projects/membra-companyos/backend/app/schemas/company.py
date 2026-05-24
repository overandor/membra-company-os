"""CompanyOS schemas — Company, Department, SOP, Memory, Initiative, KPI."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class CompanyCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    currency: Optional[str] = "USD"
    owner_wallet: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = {}


class CompanyRead(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    status: str
    currency: str
    owner_wallet: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    currency: Optional[str] = None
    owner_wallet: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class DepartmentCreate(BaseModel):
    company_id: str
    name: str
    dept_type: str
    description: Optional[str] = None
    lead_agent_id: Optional[str] = None
    kpi_json: Optional[Dict[str, Any]] = {}


class DepartmentRead(BaseModel):
    id: str
    company_id: str
    name: str
    dept_type: str
    description: Optional[str] = None
    lead_agent_id: Optional[str] = None
    sop_count: int
    active_task_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class SOPCreate(BaseModel):
    company_id: str
    department_id: Optional[str] = None
    title: str
    version: Optional[str] = "1.0"
    content: str
    steps: Optional[List[Dict[str, Any]]] = []
    triggers: Optional[List[str]] = []
    output_schema: Optional[Dict[str, Any]] = {}


class CompanyMemoryCreate(BaseModel):
    company_id: str
    memory_type: str
    key: str
    value: Optional[Dict[str, Any]] = {}
    importance_score: Optional[float] = 0.0
    source_agent_id: Optional[str] = None


class InitiativeCreate(BaseModel):
    company_id: str
    title: str
    description: Optional[str] = None
    priority: Optional[int] = 5
    target_kpi_json: Optional[Dict[str, Any]] = {}


class InitiativeRead(BaseModel):
    id: str
    company_id: str
    title: str
    status: str
    priority: int
    bottleneck_notes: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class KPIRecordCreate(BaseModel):
    company_id: str
    kpi_name: str
    kpi_category: str
    value: float
    unit: Optional[str] = None
    period_start: datetime
    period_end: datetime
    source: Optional[str] = None
