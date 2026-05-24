"""MEMBRA CompanyOS — Intent and Objective models (IntentOS)."""
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base, GUID


class IntentStatus(PyEnum):
    RAW = "raw"
    PARSED = "parsed"
    STRUCTURED = "structured"
    OBJECTIVES_CREATED = "objectives_created"
    ARCHIVED = "archived"


class ObjectiveStatus(PyEnum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class Intent(Base):
    __tablename__ = "intents"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    raw_text = Column(Text, nullable=False)
    parsed_json = Column(JSON, default=dict)
    structured_objective_json = Column(JSON, default=dict)
    user_wallet = Column(String(42), nullable=True, index=True)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    status = Column(Enum(IntentStatus), default=IntentStatus.RAW)
    confidence_score = Column(String(16), default="0.0")
    llm_provider = Column(String(32), nullable=True)
    llm_model = Column(String(64), nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    objectives = relationship("Objective", back_populates="intent", cascade="all, delete-orphan")


class Objective(Base):
    __tablename__ = "objectives"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    intent_id = Column(GUID(), ForeignKey("intents.id"), nullable=False)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(ObjectiveStatus), default=ObjectiveStatus.PENDING)
    priority = Column(String(16), default="medium")
    target_completion = Column(DateTime(timezone=True), nullable=True)
    success_criteria = Column(JSON, default=list)
    assigned_department = Column(String(64), nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    intent = relationship("Intent", back_populates="objectives")
    task_links = relationship("ObjectiveTaskLink", back_populates="objective", cascade="all, delete-orphan")


class ObjectiveTaskLink(Base):
    __tablename__ = "objective_task_links"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    objective_id = Column(GUID(), ForeignKey("objectives.id"), nullable=False)
    task_id = Column(GUID(), ForeignKey("tasks.id"), nullable=False)
    link_type = Column(String(32), default="primary")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    objective = relationship("Objective", back_populates="task_links")
    task = relationship("Task", back_populates="objective_links")
