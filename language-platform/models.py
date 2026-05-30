"""
CollateralOps — SQLAlchemy models for the software collateral execution desk.
"""
import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Boolean, DateTime,
    Text, ForeignKey, Enum, JSON, Index
)
from sqlalchemy.orm import declarative_base, relationship, Session

Base = declarative_base()


def _gen_id() -> str:
    return str(uuid.uuid4())[:8]


class AssetType(str, enum.Enum):
    REPO = "repo"
    MODULE = "module"
    API = "api"
    DATASET = "dataset"
    MODEL = "model"


class AssetStatus(str, enum.Enum):
    ACTIVE = "active"
    IMPROVING = "improving"
    REVIEW = "review"
    RISK_BLOCKED = "risk_blocked"
    ARCHIVED = "archived"


class Asset(Base):
    __tablename__ = "assets"

    id = Column(String(16), primary_key=True, default=_gen_id)
    name = Column(String(255), nullable=False, index=True)
    type = Column(Enum(AssetType), nullable=False, default=AssetType.REPO)
    status = Column(Enum(AssetStatus), nullable=False, default=AssetStatus.ACTIVE)
    strategic_value = Column(Float, default=0.0)
    buyer_today_value = Column(Float, default=0.0)
    liquidation_value = Column(Float, default=0.0)
    collateral_support = Column(Float, default=0.0)
    financeability_score = Column(Float, default=0.0)
    risk_score = Column(Float, default=0.0)
    lines_of_code = Column(Integer, default=0)
    last_commit = Column(DateTime, nullable=True)
    tech_stack = Column(JSON, default=list)
    repo_url = Column(String(512), nullable=True)
    owner = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    valuations: List["ValuationSet"] = relationship("ValuationSet", back_populates="asset", cascade="all, delete-orphan")
    proofs: List["ProofEvent"] = relationship("ProofEvent", back_populates="asset", cascade="all, delete-orphan")
    risks: List["RiskFlag"] = relationship("RiskFlag", back_populates="asset", cascade="all, delete-orphan")
    packet_sections: List["PacketSection"] = relationship("PacketSection", back_populates="asset", cascade="all, delete-orphan")
    improvements: List["ImprovementTask"] = relationship("ImprovementTask", back_populates="asset", cascade="all, delete-orphan")
    agent_work: List["AgentWorkRecord"] = relationship("AgentWorkRecord", back_populates="asset", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_asset_status_score", "status", "financeability_score"),
    )


class ValuationSet(Base):
    __tablename__ = "valuation_sets"

    id = Column(String(16), primary_key=True, default=_gen_id)
    asset_id = Column(String(16), ForeignKey("assets.id"), nullable=False)
    method = Column(String(64), nullable=False)  # DCF, market, cost, liquidation
    value = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    asset: Asset = relationship("Asset", back_populates="valuations")


class ProofEvent(Base):
    __tablename__ = "proof_events"

    id = Column(String(16), primary_key=True, default=_gen_id)
    asset_id = Column(String(16), ForeignKey("assets.id"), nullable=False)
    event_type = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    hash = Column(String(64), nullable=False)
    prev_hash = Column(String(64), nullable=True)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    asset: Asset = relationship("Asset", back_populates="proofs")

    __table_args__ = (
        Index("ix_proof_asset_time", "asset_id", "created_at"),
    )


class RiskFlag(Base):
    __tablename__ = "risk_flags"

    id = Column(String(16), primary_key=True, default=_gen_id)
    asset_id = Column(String(16), ForeignKey("assets.id"), nullable=False)
    category = Column(String(64), nullable=False)  # ownership, security, license, originality
    severity = Column(String(16), nullable=False, default="medium")  # low, medium, high, critical
    reason = Column(Text, nullable=False)
    remediation = Column(Text, nullable=True)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    asset: Asset = relationship("Asset", back_populates="risks")


class PacketSection(Base):
    __tablename__ = "packet_sections"

    id = Column(String(16), primary_key=True, default=_gen_id)
    asset_id = Column(String(16), ForeignKey("assets.id"), nullable=False)
    section_key = Column(String(64), nullable=False)
    title = Column(String(255), nullable=False)
    is_complete = Column(Boolean, default=False)
    completeness = Column(Float, default=0.0)
    evidence_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)

    asset: Asset = relationship("Asset", back_populates="packet_sections")


class BuyerTarget(Base):
    __tablename__ = "buyer_targets"

    id = Column(String(16), primary_key=True, default=_gen_id)
    asset_id = Column(String(16), ForeignKey("assets.id"), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(64), nullable=False)  # strategic, financial, acqui-hire
    probability = Column(Float, default=0.0)
    estimated_recovery = Column(Float, default=0.0)
    rationale = Column(Text, nullable=True)
    contact_status = Column(String(64), default="not_contacted")
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentWorkRecord(Base):
    __tablename__ = "agent_work_records"

    id = Column(String(16), primary_key=True, default=_gen_id)
    asset_id = Column(String(16), ForeignKey("assets.id"), nullable=False)
    agent_name = Column(String(128), nullable=False)
    action = Column(String(255), nullable=False)
    files_created = Column(Integer, default=0)
    files_modified = Column(Integer, default=0)
    tests_added = Column(Integer, default=0)
    docs_added = Column(Integer, default=0)
    lines_added = Column(Integer, default=0)
    lines_deleted = Column(Integer, default=0)
    build_status = Column(String(32), default="unknown")
    duration_minutes = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    asset: Asset = relationship("Asset", back_populates="agent_work")


class ImprovementTask(Base):
    __tablename__ = "improvement_tasks"

    id = Column(String(16), primary_key=True, default=_gen_id)
    asset_id = Column(String(16), ForeignKey("assets.id"), nullable=False)
    title = Column(String(255), nullable=False)
    category = Column(String(64), nullable=False)  # documentation, testing, security, legal, coverage
    impact_estimate = Column(Float, default=0.0)  # points to financeability score
    effort_estimate = Column(String(16), default="medium")  # small, medium, large
    is_completed = Column(Boolean, default=False)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    asset: Asset = relationship("Asset", back_populates="improvements")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(16), primary_key=True, default=_gen_id)
    event_type = Column(String(64), nullable=False)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(16), nullable=False)
    user = Column(String(128), nullable=True)
    payload = Column(JSON, default=dict)
    hash = Column(String(64), nullable=False)
    prev_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_audit_entity", "entity_type", "entity_id", "created_at"),
    )


# Engine and session factory
_engine: Optional[object] = None


def get_engine(db_path: str = "collateralops.db"):
    global _engine
    if _engine is None:
        _engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(_engine)
    return _engine


def get_session(db_path: str = "collateralops.db") -> Session:
    return Session(get_engine(db_path))
