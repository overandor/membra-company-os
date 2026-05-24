"""MEMBRA CompanyOS — Workforce models for 60 LLM employees."""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Integer, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base, GUID


class WorkforceEmployee(Base):
    __tablename__ = "workforce_employees"

    id = Column(GUID(), primary_key=True)
    employee_id = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    department = Column(String(32), nullable=False, index=True)
    title = Column(String(128), nullable=False)
    model = Column(String(64), nullable=False, default="llama3.2")
    status = Column(String(16), nullable=False, default="idle")  # idle, running, error, offline
    system_prompt = Column(Text, nullable=False)
    responsibilities = Column(JSON, default=list)
    last_run_at = Column(DateTime, nullable=True)
    total_runs = Column(Integer, nullable=False, default=0)
    total_contributions = Column(Integer, nullable=False, default=0)
    last_output = Column(Text, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    contributions = relationship("WorkforceContribution", back_populates="employee", cascade="all, delete-orphan")


class WorkforceContribution(Base):
    __tablename__ = "workforce_contributions"

    id = Column(GUID(), primary_key=True)
    employee_id = Column(String(32), ForeignKey("workforce_employees.employee_id"), nullable=False, index=True)
    department = Column(String(32), nullable=False, index=True)
    task_type = Column(String(64), nullable=False)
    prompt = Column(Text, nullable=True)
    output = Column(Text, nullable=True)
    output_summary = Column(String(256), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    employee = relationship("WorkforceEmployee", back_populates="contributions")


class WorkforceTask(Base):
    __tablename__ = "workforce_tasks"

    id = Column(GUID(), primary_key=True)
    employee_id = Column(String(32), ForeignKey("workforce_employees.employee_id"), nullable=False, index=True)
    department = Column(String(32), nullable=False, index=True)
    task_description = Column(Text, nullable=False)
    status = Column(String(16), nullable=False, default="pending")  # pending, running, completed, failed
    priority = Column(Integer, nullable=False, default=3)
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
