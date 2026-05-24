"""AgentOS schemas — Agent, Tool, Action Log."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class AgentCreate(BaseModel):
    agent_type: str
    name: str
    description: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    system_prompt: Optional[str] = None
    allowed_actions: Optional[List[str]] = []
    blocked_actions: Optional[List[str]] = []
    output_schema: Optional[Dict[str, Any]] = {}
    permissions: Optional[List[str]] = []
    company_id: Optional[str] = None
    department_id: Optional[str] = None
    owner_wallet: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = {}


class AgentRead(BaseModel):
    id: str
    agent_type: str
    name: str
    description: Optional[str] = None
    status: str
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    allowed_actions: Optional[List[str]] = []
    blocked_actions: Optional[List[str]] = []
    output_schema: Optional[Dict[str, Any]] = {}
    permissions: Optional[List[str]] = []
    company_id: Optional[str] = None
    department_id: Optional[str] = None
    owner_wallet: Optional[str] = None
    version: str
    execution_count: int
    success_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    system_prompt: Optional[str] = None
    allowed_actions: Optional[List[str]] = None
    blocked_actions: Optional[List[str]] = None
    permissions: Optional[List[str]] = None
    metadata_json: Optional[Dict[str, Any]] = None


class AgentToolCreate(BaseModel):
    agent_id: str
    tool_name: str
    tool_description: Optional[str] = None
    tool_schema: Optional[Dict[str, Any]] = {}
    requires_human_approval: bool = False
    rate_limit_per_minute: Optional[int] = 60


class AgentActionLogRead(BaseModel):
    id: str
    agent_id: str
    action_type: str
    task_id: Optional[str] = None
    job_id: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = {}
    output_data: Optional[Dict[str, Any]] = {}
    status: str
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    proof_hash: Optional[str] = None
    governance_gate_passed: bool
    created_at: datetime

    class Config:
        from_attributes = True
