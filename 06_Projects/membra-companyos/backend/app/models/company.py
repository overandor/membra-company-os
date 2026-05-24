"""MEMBRA CompanyOS — Company, department, SOP, memory, initiative, KPI models."""
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Enum, Text, JSON, Numeric, Integer
from sqlalchemy.orm import relationship
from app.db.base import Base, GUID


class CompanyStatus(PyEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DISSOLVED = "dissolved"


class DepartmentType(PyEnum):
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


class InitiativeStatus(PyEnum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Company(Base):
    __tablename__ = "companies"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(CompanyStatus), default=CompanyStatus.DRAFT)
    currency = Column(String(3), default="USD")
    owner_wallet = Column(String(42), nullable=True, index=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    members = relationship("User", back_populates="company")
    departments = relationship("Department", back_populates="company", cascade="all, delete-orphan")
    sops = relationship("SOP", back_populates="company", cascade="all, delete-orphan")
    memories = relationship("CompanyMemory", back_populates="company", cascade="all, delete-orphan")
    initiatives = relationship("Initiative", back_populates="company", cascade="all, delete-orphan")
    kpi_records = relationship("KPIRecord", back_populates="company", cascade="all, delete-orphan")


class Department(Base):
    __tablename__ = "departments"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=False)
    name = Column(String(255), nullable=False)
    dept_type = Column(Enum(DepartmentType), nullable=False)
    description = Column(Text, nullable=True)
    lead_agent_id = Column(GUID(), ForeignKey("agents.id"), nullable=True)
    sop_count = Column(Integer, default=0)
    active_task_count = Column(Integer, default=0)
    kpi_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="departments")
    sops = relationship("SOP", back_populates="department")


class SOP(Base):
    __tablename__ = "sops"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=False)
    department_id = Column(GUID(), ForeignKey("departments.id"), nullable=True)
    title = Column(String(255), nullable=False)
    version = Column(String(16), default="1.0")
    content = Column(Text, nullable=False)
    steps = Column(JSON, default=list)
    triggers = Column(JSON, default=list)
    output_schema = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="sops")
    department = relationship("Department", back_populates="sops")


class CompanyMemory(Base):
    __tablename__ = "company_memories"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=False)
    memory_type = Column(String(64), nullable=False)
    key = Column(String(255), nullable=False)
    value = Column(JSON, default=dict)
    importance_score = Column(Numeric(5, 2), default=0.0)
    source_agent_id = Column(GUID(), ForeignKey("agents.id"), nullable=True)
    proof_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="memories")


class Initiative(Base):
    __tablename__ = "initiatives"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(InitiativeStatus), default=InitiativeStatus.PROPOSED)
    priority = Column(Integer, default=5)
    target_kpi_json = Column(JSON, default=dict)
    bottleneck_notes = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="initiatives")


class KPIRecord(Base):
    __tablename__ = "kpi_records"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=False)
    kpi_name = Column(String(255), nullable=False)
    kpi_category = Column(String(64), nullable=False)
    value = Column(Numeric(20, 6), nullable=False)
    unit = Column(String(32), nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    source = Column(String(255), nullable=True)
    proof_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="kpi_records")
