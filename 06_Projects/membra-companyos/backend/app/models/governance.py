"""MEMBRA CompanyOS — Governance, approval, policy, consent, risk, escalation models (GovernanceOS)."""
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, JSON, Boolean, Integer
from sqlalchemy.orm import relationship
from app.db.base import Base, GUID


class ApprovalStatus(PyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    AUTO_APPROVED = "auto_approved"
    EXPIRED = "expired"


class PolicyStatus(PyEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    EMERGENCY = "emergency"


class RiskLevel(PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConsentType(PyEnum):
    OWNER_VISIBILITY = "owner_visibility"
    DATA_SHARING = "data_sharing"
    SETTLEMENT_AUTH = "settlement_auth"
    ASSET_USE = "asset_use"
    AI_DECISION = "ai_decision"


class ApprovalGate(Base):
    __tablename__ = "approval_gates"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    gate_type = Column(String(64), nullable=False)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(GUID(), nullable=False)
    requester_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    requester_agent_id = Column(GUID(), ForeignKey("agents.id"), nullable=True)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.LOW)
    approvers = Column(JSON, default=list)
    required_approvals = Column(Integer, default=1)
    current_approvals = Column(Integer, default=0)
    rejections = Column(Integer, default=0)
    decision_notes = Column(Text, nullable=True)
    auto_expire_hours = Column(Integer, default=48)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    proof_hash = Column(String(64), nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Policy(Base):
    __tablename__ = "policies"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=True)
    name = Column(String(255), nullable=False)
    version = Column(String(16), default="1.0")
    status = Column(Enum(PolicyStatus), default=PolicyStatus.DRAFT)
    policy_type = Column(String(64), nullable=False)
    content = Column(Text, nullable=False)
    rules = Column(JSON, default=list)
    applies_to = Column(JSON, default=list)
    enforcement_mode = Column(String(32), default="audit")
    created_by = Column(GUID(), ForeignKey("users.id"), nullable=True)
    effective_date = Column(DateTime(timezone=True), nullable=True)
    deprecated_at = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    consent_type = Column(Enum(ConsentType), nullable=False)
    owner_wallet = Column(String(42), nullable=False, index=True)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(GUID(), nullable=False)
    granted = Column(Boolean, default=False)
    granted_by = Column(GUID(), ForeignKey("users.id"), nullable=True)
    granted_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    proof_hash = Column(String(64), nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class RiskClassification(Base):
    __tablename__ = "risk_classifications"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(GUID(), nullable=False)
    risk_type = Column(String(64), nullable=False)
    risk_level = Column(Enum(RiskLevel), nullable=False)
    description = Column(Text, nullable=True)
    mitigation = Column(Text, nullable=True)
    flagged_by = Column(GUID(), ForeignKey("users.id"), nullable=True)
    flagged_agent_id = Column(GUID(), ForeignKey("agents.id"), nullable=True)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class EscalationRule(Base):
    __tablename__ = "escalation_rules"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=True)
    name = Column(String(255), nullable=False)
    trigger_condition = Column(String(255), nullable=False)
    trigger_rules = Column(JSON, default=list)
    escalation_path = Column(JSON, default=list)
    notify_wallets = Column(JSON, default=list)
    auto_action = Column(String(64), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
