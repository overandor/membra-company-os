"""MEMBRA CompanyOS — Agent registry, tools, action logs (AgentOS)."""
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, JSON, Boolean, Integer
from sqlalchemy.orm import relationship
from app.db.base import Base, GUID


class AgentType(PyEnum):
    STRATEGY = "strategy"
    PRODUCT = "product"
    ENGINEERING = "engineering"
    OPERATIONS = "operations"
    SALES = "sales"
    FINANCE = "finance"
    LEGAL_RISK = "legal_risk"
    GOVERNANCE = "governance"
    PROOF = "proof"
    CONCIERGE = "concierge"


class AgentStatus(PyEnum):
    REGISTERED = "registered"
    ACTIVE = "active"
    PAUSED = "paused"
    REVOKED = "revoked"


class Agent(Base):
    __tablename__ = "agents"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    agent_type = Column(Enum(AgentType), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(AgentStatus), default=AgentStatus.REGISTERED)
    llm_provider = Column(String(32), nullable=True)
    llm_model = Column(String(64), nullable=True)
    system_prompt = Column(Text, nullable=True)
    allowed_actions = Column(JSON, default=list)
    blocked_actions = Column(JSON, default=list)
    output_schema = Column(JSON, default=dict)
    permissions = Column(JSON, default=list)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=True)
    department_id = Column(GUID(), ForeignKey("departments.id"), nullable=True)
    owner_wallet = Column(String(42), nullable=True)
    version = Column(String(16), default="1.0")
    execution_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    tools = relationship("AgentTool", back_populates="agent", cascade="all, delete-orphan")
    action_logs = relationship("AgentActionLog", back_populates="agent", cascade="all, delete-orphan")


class AgentTool(Base):
    __tablename__ = "agent_tools"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    agent_id = Column(GUID(), ForeignKey("agents.id"), nullable=False)
    tool_name = Column(String(128), nullable=False)
    tool_description = Column(Text, nullable=True)
    tool_schema = Column(JSON, default=dict)
    is_enabled = Column(Boolean, default=True)
    requires_human_approval = Column(Boolean, default=False)
    rate_limit_per_minute = Column(Integer, default=60)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    agent = relationship("Agent", back_populates="tools")


class AgentActionLog(Base):
    __tablename__ = "agent_action_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    agent_id = Column(GUID(), ForeignKey("agents.id"), nullable=False)
    action_type = Column(String(64), nullable=False)
    task_id = Column(GUID(), ForeignKey("tasks.id"), nullable=True)
    job_id = Column(GUID(), ForeignKey("jobs.id"), nullable=True)
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    status = Column(String(32), default="success")
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    proof_hash = Column(String(64), nullable=True)
    governance_gate_passed = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    agent = relationship("Agent", back_populates="action_logs")
