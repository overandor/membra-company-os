"""MEMBRA CompanyOS — Job, bounty, work order, marketplace, proof models (JobOS)."""
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, JSON, Numeric, Integer, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base, GUID


class JobStatus(PyEnum):
    DRAFT = "draft"
    POSTED = "posted"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class JobType(PyEnum):
    BOUNTY = "bounty"
    WORK_ORDER = "work_order"
    MARKETPLACE_LISTING = "marketplace_listing"
    ADMIN_REVIEW = "admin_review"
    FULFILLMENT = "fulfillment"
    KPI_ANALYSIS = "kpi_analysis"
    APARTMENT_TASK = "apartment_task"
    CAR_AD_TASK = "car_ad_task"
    WINDOW_AD_TASK = "window_ad_task"
    WEARABLE_TASK = "wearable_task"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    task_id = Column(GUID(), ForeignKey("tasks.id"), nullable=True)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    job_type = Column(Enum(JobType), nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.DRAFT)
    budget = Column(Numeric(20, 6), nullable=True)
    currency = Column(String(3), default="USD")
    payout_eligible = Column(Boolean, default=False)
    payout_amount = Column(Numeric(20, 6), default=0)
    assigned_to = Column(GUID(), ForeignKey("users.id"), nullable=True)
    assigned_agent_id = Column(GUID(), ForeignKey("agents.id"), nullable=True)
    asset_id = Column(GUID(), ForeignKey("world_assets.id"), nullable=True)
    location_json = Column(JSON, default=dict)
    requirements = Column(JSON, default=list)
    deliverables = Column(JSON, default=list)
    deadline = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    proof_hash = Column(String(64), nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    proofs = relationship("JobProof", back_populates="job", cascade="all, delete-orphan")


class Bounty(Base):
    __tablename__ = "bounties"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    job_id = Column(GUID(), ForeignKey("jobs.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    reward_amount = Column(Numeric(20, 6), nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(String(32), default="open")
    requirements = Column(JSON, default=list)
    submissions_count = Column(Integer, default=0)
    winner_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    deadline = Column(DateTime(timezone=True), nullable=True)


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    job_id = Column(GUID(), ForeignKey("jobs.id"), nullable=True)
    wo_number = Column(String(64), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    crew_assignment = Column(JSON, default=list)
    schedule_json = Column(JSON, default=dict)
    equipment_json = Column(JSON, default=list)
    cost_estimate = Column(Numeric(20, 6), nullable=True)
    actual_cost = Column(Numeric(20, 6), nullable=True)
    status = Column(String(32), default="scheduled")
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class MarketplaceAction(Base):
    __tablename__ = "marketplace_actions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    job_id = Column(GUID(), ForeignKey("jobs.id"), nullable=True)
    action_type = Column(String(64), nullable=False)
    asset_type = Column(String(64), nullable=False)
    asset_id = Column(GUID(), ForeignKey("world_assets.id"), nullable=True)
    listing_price = Column(Numeric(20, 6), nullable=True)
    status = Column(String(32), default="draft")
    visibility = Column(String(32), default="private")
    owner_consent = Column(Boolean, default=False)
    governance_approved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    published_at = Column(DateTime(timezone=True), nullable=True)


class JobProof(Base):
    __tablename__ = "job_proofs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    job_id = Column(GUID(), ForeignKey("jobs.id"), nullable=False)
    proof_type = Column(String(64), nullable=False)
    proof_data = Column(JSON, default=dict)
    ipfs_cid = Column(String(64), nullable=True)
    verification_status = Column(String(32), default="pending")
    verified_by = Column(GUID(), ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    proof_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    job = relationship("Job", back_populates="proofs")
