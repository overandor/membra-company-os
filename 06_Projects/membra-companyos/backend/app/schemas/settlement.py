"""SettlementOS schemas — Record, Payout, RailLog."""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class SettlementRecordCreate(BaseModel):
    company_id: Optional[str] = None
    eligibility_id: Optional[str] = None
    job_id: Optional[str] = None
    recipient_type: str
    recipient_id: str
    recipient_wallet: Optional[str] = None
    amount: float
    currency: Optional[str] = "USD"
    rail: str
    fee_amount: Optional[float] = 0
    metadata_json: Optional[Dict[str, Any]] = {}


class SettlementRecordRead(BaseModel):
    id: str
    company_id: Optional[str] = None
    eligibility_id: Optional[str] = None
    job_id: Optional[str] = None
    recipient_type: str
    recipient_id: str
    recipient_wallet: Optional[str] = None
    amount: float
    currency: str
    rail: str
    status: str
    instructions_sent_at: Optional[datetime] = None
    settled_at: Optional[datetime] = None
    external_tx_id: Optional[str] = None
    fee_amount: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PayoutInstructionCreate(BaseModel):
    settlement_id: str
    instruction_type: str
    payload: Optional[Dict[str, Any]] = {}


class ExternalRailLogCreate(BaseModel):
    settlement_id: str
    rail: str
    event_type: str
    request_payload: Optional[Dict[str, Any]] = {}
    response_payload: Optional[Dict[str, Any]] = {}
    status_code: Optional[str] = None
    error_message: Optional[str] = None
