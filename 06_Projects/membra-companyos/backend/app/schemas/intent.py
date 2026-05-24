"""IntentOS schemas — Intent, Objective."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class IntentCreate(BaseModel):
    raw_text: str
    user_wallet: Optional[str] = None
    user_id: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = {}


class IntentRead(BaseModel):
    id: str
    raw_text: str
    parsed_json: Optional[Dict[str, Any]] = {}
    structured_objective_json: Optional[Dict[str, Any]] = {}
    user_wallet: Optional[str] = None
    user_id: Optional[str] = None
    status: str
    confidence_score: str
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IntentUpdate(BaseModel):
    parsed_json: Optional[Dict[str, Any]] = None
    structured_objective_json: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    confidence_score: Optional[str] = None


class ObjectiveCreate(BaseModel):
    intent_id: str
    title: str
    description: Optional[str] = None
    company_id: Optional[str] = None
    priority: Optional[str] = "medium"
    target_completion: Optional[datetime] = None
    success_criteria: Optional[List[str]] = []
    assigned_department: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = {}


class ObjectiveRead(BaseModel):
    id: str
    intent_id: str
    company_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    target_completion: Optional[datetime] = None
    success_criteria: Optional[List[str]] = []
    assigned_department: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ObjectiveUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    target_completion: Optional[datetime] = None
    success_criteria: Optional[List[str]] = None
