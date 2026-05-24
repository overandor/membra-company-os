"""MEMBRA CompanyOS — ProofBook, proof chain, decision events, settlement eligibility (ProofBook)."""
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base, GUID


class ProofEntryType(PyEnum):
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    AGENT_ACTION = "agent_action"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_REJECTED = "approval_rejected"
    POLICY_APPLIED = "policy_applied"
    LISTING_PUBLISHED = "listing_published"
    JOB_COMPLETED = "job_completed"
    SETTLEMENT_TRIGGERED = "settlement_triggered"
    KPI_RECORDED = "kpi_recorded"
    CONSENT_GRANTED = "consent_granted"
    CONSENT_REVOKED = "consent_revoked"
    ASSET_RESERVED = "asset_reserved"
    DECISION_MADE = "decision_made"
    EXTERNAL_SETTLEMENT = "external_settlement"


class ProofBookEntry(Base):
    __tablename__ = "proofbook_entries"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    entry_type = Column(Enum(ProofEntryType), nullable=False)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=True)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(GUID(), nullable=False)
    actor_type = Column(String(16), nullable=False)
    actor_id = Column(GUID(), nullable=False)
    description = Column(Text, nullable=True)
    data = Column(JSON, default=dict)
    ipfs_cid = Column(String(64), nullable=True)
    proof_hash = Column(String(64), nullable=False, index=True)
    previous_hash = Column(String(64), nullable=True)
    chain_id = Column(GUID(), ForeignKey("proof_chains.id"), nullable=True)
    block_number = Column(String(64), nullable=True)
    tx_hash = Column(String(66), nullable=True)
    verified = Column(Boolean, default=False)
    verification_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    chain = relationship("ProofChain", back_populates="entries")


class ProofChain(Base):
    __tablename__ = "proof_chains"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=True)
    chain_name = Column(String(255), nullable=False)
    chain_type = Column(String(64), default="internal")
    genesis_hash = Column(String(64), nullable=False)
    latest_hash = Column(String(64), nullable=False)
    entry_count = Column(String(16), default="0")
    anchored_to = Column(String(255), nullable=True)
    anchor_tx = Column(String(66), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    entries = relationship("ProofBookEntry", back_populates="chain", cascade="all, delete-orphan")


class DecisionEvent(Base):
    __tablename__ = "decision_events"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=True)
    decision_type = Column(String(64), nullable=False)
    subject_type = Column(String(64), nullable=False)
    subject_id = Column(GUID(), nullable=False)
    decision_maker_type = Column(String(16), nullable=False)
    decision_maker_id = Column(GUID(), nullable=False)
    rationale = Column(Text, nullable=True)
    alternatives = Column(JSON, default=list)
    selected_option = Column(String(255), nullable=True)
    confidence_score = Column(String(16), default="0.0")
    human_approved = Column(Boolean, nullable=True)
    approved_by = Column(GUID(), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    proof_hash = Column(String(64), nullable=False)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SettlementEligibility(Base):
    __tablename__ = "settlement_eligibilities"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    job_id = Column(GUID(), ForeignKey("jobs.id"), nullable=True)
    work_order_id = Column(GUID(), ForeignKey("work_orders.id"), nullable=True)
    bounty_id = Column(GUID(), ForeignKey("bounties.id"), nullable=True)
    recipient_wallet = Column(String(42), nullable=True)
    recipient_user_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    eligible_amount = Column(String(64), nullable=False)
    currency = Column(String(3), default="USD")
    criteria_met = Column(JSON, default=list)
    governance_approved = Column(Boolean, default=False)
    proof_hash = Column(String(64), nullable=False)
    status = Column(String(32), default="pending")
    processed_at = Column(DateTime(timezone=True), nullable=True)
    external_tx_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
