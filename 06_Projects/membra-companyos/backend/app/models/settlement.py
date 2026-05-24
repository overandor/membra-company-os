"""MEMBRA CompanyOS — Settlement, payout, external rail logs (SettlementOS)."""
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, JSON, Numeric
from sqlalchemy.orm import relationship
from app.db.base import Base, GUID


class SettlementStatus(PyEnum):
    PENDING = "pending"
    ELIGIBLE = "eligible"
    INSTRUCTIONS_SENT = "instructions_sent"
    PROCESSING = "processing"
    SETTLED = "settled"
    FAILED = "failed"
    DISPUTED = "disputed"


class SettlementRail(PyEnum):
    STRIPE = "stripe"
    SOLANA = "solana"
    ETHEREUM = "ethereum"
    BANK_TRANSFER = "bank_transfer"
    CRYPTO_OTHER = "crypto_other"


class SettlementRecord(Base):
    __tablename__ = "settlement_records"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=True)
    eligibility_id = Column(GUID(), ForeignKey("settlement_eligibilities.id"), nullable=True)
    job_id = Column(GUID(), ForeignKey("jobs.id"), nullable=True)
    recipient_type = Column(String(16), nullable=False)
    recipient_id = Column(GUID(), nullable=False)
    recipient_wallet = Column(String(42), nullable=True)
    amount = Column(Numeric(20, 6), nullable=False)
    currency = Column(String(3), default="USD")
    rail = Column(Enum(SettlementRail), nullable=False)
    status = Column(Enum(SettlementStatus), default=SettlementStatus.PENDING)
    instructions_sent_at = Column(DateTime(timezone=True), nullable=True)
    settled_at = Column(DateTime(timezone=True), nullable=True)
    external_tx_id = Column(String(255), nullable=True)
    fee_amount = Column(Numeric(20, 6), default=0)
    metadata_json = Column(JSON, default=dict)
    proof_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    payouts = relationship("PayoutInstruction", back_populates="settlement", cascade="all, delete-orphan")
    rail_logs = relationship("ExternalRailLog", back_populates="settlement", cascade="all, delete-orphan")


class PayoutInstruction(Base):
    __tablename__ = "payout_instructions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    settlement_id = Column(GUID(), ForeignKey("settlement_records.id"), nullable=False)
    instruction_type = Column(String(64), nullable=False)
    payload = Column(JSON, default=dict)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    response_code = Column(String(16), nullable=True)
    response_body = Column(Text, nullable=True)
    retry_count = Column(String(16), default="0")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    settlement = relationship("SettlementRecord", back_populates="payouts")


class ExternalRailLog(Base):
    __tablename__ = "external_rail_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    settlement_id = Column(GUID(), ForeignKey("settlement_records.id"), nullable=False)
    rail = Column(Enum(SettlementRail), nullable=False)
    event_type = Column(String(64), nullable=False)
    request_payload = Column(JSON, default=dict)
    response_payload = Column(JSON, default=dict)
    status_code = Column(String(16), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    settlement = relationship("SettlementRecord", back_populates="rail_logs")
