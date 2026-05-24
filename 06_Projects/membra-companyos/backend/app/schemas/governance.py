"""GovernanceOS schemas — ApprovalGate, Policy, Consent, Risk, Escalation."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class ApprovalGateCreate(BaseModel):
    gate_type: str
    resource_type: str
    resource_id: str
    requester_id: Optional[str] = None
    requester_agent_id: Optional[str] = None
    risk_level: Optional[str] = "low"
    approvers: Optional[List[str]] = []
    required_approvals: Optional[int] = 1
    auto_expire_hours: Optional[int] = 48
    metadata_json: Optional[Dict[str, Any]] = {}


class ApprovalGateRead(BaseModel):
    id: str
    gate_type: str
    resource_type: str
    resource_id: str
    status: str
    risk_level: str
    required_approvals: int
    current_approvals: int
    rejections: int
    decision_notes: Optional[str] = None
    expires_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PolicyCreate(BaseModel):
    company_id: Optional[str] = None
    name: str
    version: Optional[str] = "1.0"
    policy_type: str
    content: str
    rules: Optional[List[Dict[str, Any]]] = []
    applies_to: Optional[List[str]] = []
    enforcement_mode: Optional[str] = "audit"
    effective_date: Optional[datetime] = None


class PolicyRead(BaseModel):
    id: str
    name: str
    version: str
    status: str
    policy_type: str
    content: str
    rules: Optional[List[Dict[str, Any]]] = []
    applies_to: Optional[List[str]] = []
    enforcement_mode: str
    effective_date: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConsentRecordCreate(BaseModel):
    consent_type: str
    owner_wallet: str
    resource_type: str
    resource_id: str
    granted: Optional[bool] = False
    granted_by: Optional[str] = None
    expires_at: Optional[datetime] = None
    metadata_json: Optional[Dict[str, Any]] = {}


class RiskClassificationCreate(BaseModel):
    resource_type: str
    resource_id: str
    risk_type: str
    risk_level: str
    description: Optional[str] = None
    mitigation: Optional[str] = None
    flagged_by: Optional[str] = None
    flagged_agent_id: Optional[str] = None


class EscalationRuleCreate(BaseModel):
    company_id: Optional[str] = None
    name: str
    trigger_condition: str
    trigger_rules: Optional[List[Dict[str, Any]]] = []
    escalation_path: Optional[List[str]] = []
    notify_wallets: Optional[List[str]] = []
    auto_action: Optional[str] = None
