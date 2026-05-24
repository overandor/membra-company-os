from typing import Any, Dict, List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field

class AgentCapability(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)

class AgentMetadata(BaseModel):
    id: str
    name: str
    description: str
    category: str
    version: str = "1.0.0"
    capabilities: List[AgentCapability] = Field(default_factory=list)
    price_per_run: int = 100  # cents
    model: str = "gpt-4o"
    supported_llms: List[str] = Field(default_factory=list)
    endpoints: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    author: str = "AgentWorkforce"

class AgentRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    webhook_url: Optional[str] = None
    notify_email: Optional[str] = None
    notify_sms: Optional[str] = None
    deploy_to_vercel: bool = False
    create_repo: bool = False
    repo_name: Optional[str] = None

class AgentResult(BaseModel):
    agent_id: str
    status: Literal["success", "error", "pending"] = "success"
    output: Any
    tokens_used: int = 0
    cost_usd: float = 0.0
    execution_time_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    deployment_url: Optional[str] = None
    repo_url: Optional[str] = None

class WorkerAppraisal(BaseModel):
    agent_id: str
    code_value: int = 800
    ip_value: int = 500
    infra_value: int = 300
    doc_value: int = 200
    provenance_value: int = 200
    complexity_premium: int = 0
    revenue_premium: int = 0
    total_value: int = 2000
    roi_annual: float = 45.0
    payback_months: float = 6.0
    hourly_rate: float = 50.0
    maintenance_monthly: float = 400.0
    revenue_year1_low: float = 0.0
    revenue_year1_high: float = 0.0
    quality_score: int = 72
    risk_level: str = "medium"
    certification: str = "ISO/IEC 27001"
    last_appraisal: datetime = Field(default_factory=datetime.utcnow)

class StripeCheckoutRequest(BaseModel):
    agent_id: str
    success_url: str
    cancel_url: str
    quantity: int = 1
    customer_email: Optional[str] = None

class StripeCheckoutResponse(BaseModel):
    session_id: str
    url: str

class TwilioNotificationRequest(BaseModel):
    to: str
    message: str
    agent_id: Optional[str] = None
    media_url: Optional[str] = None

class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str
    html: Optional[str] = None
    agent_id: Optional[str] = None

class VercelDeployRequest(BaseModel):
    repo_url: str
    project_name: str
    framework: Optional[str] = "nextjs"
    env_vars: Optional[Dict[str, str]] = Field(default_factory=dict)

class VercelDeployResponse(BaseModel):
    project_id: str
    deployment_url: str
    status: str

class GitHubRepoRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    private: bool = True
    template: Optional[str] = None
    readme_content: Optional[str] = None

class GitHubRepoResponse(BaseModel):
    repo_url: str
    clone_url: str
    created: bool

class BillingRecord(BaseModel):
    agent_id: str
    customer_id: str
    amount_cents: int
    currency: str = "usd"
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UserCreate(BaseModel):
    email: str
    name: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    role: Optional[str] = "user"


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    role: str
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScheduleCreate(BaseModel):
    agent_id: str
    name: str
    query: str
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    cron: str = "0 */6 * * *"  # Every 6 hours by default
    notify_email: Optional[str] = None


class ScheduleResponse(BaseModel):
    id: str
    agent_id: str
    name: str
    query: str
    context: Optional[Dict[str, Any]] = None
    cron: str
    is_active: bool
    notify_email: Optional[str] = None
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    run_count: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
