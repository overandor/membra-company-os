"""ProofBook schemas — Entry, Chain, DecisionEvent, SettlementEligibility."""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ProofBookEntryCreate(BaseModel):
    entry_type: str
    company_id: Optional[str] = None
    resource_type: str
    resource_id: str
    actor_type: str
    actor_id: str
    description: Optional[str] = None
    data: Optional[Dict[str, Any]] = {}
    ipfs_cid: Optional[str] = None
    proof_hash: str
    previous_hash: Optional[str] = None
    chain_id: Optional[str] = None
    block_number: Optional[str] = None
    tx_hash: Optional[str] = None


class ProofBookEntryRead(BaseModel):
    id: str
    entry_type: str
    company_id: Optional[str] = None
    resource_type: str
    resource_id: str
    actor_type: str
    actor_id: str
    description: Optional[str] = None
    data: Optional[Dict[str, Any]] = {}
    ipfs_cid: Optional[str] = None
    proof_hash: str
    previous_hash: Optional[str] = None
    chain_id: Optional[str] = None
    verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ProofChainCreate(BaseModel):
    company_id: Optional[str] = None
    chain_name: str
    chain_type: Optional[str] = "internal"
    genesis_hash: str
    latest_hash: str
    anchored_to: Optional[str] = None


class ProofChainRead(BaseModel):
    id: str
    company_id: Optional[str] = None
    chain_name: str
    chain_type: str
    genesis_hash: str
    latest_hash: str
    entry_count: str
    anchored_to: Optional[str] = None
    anchor_tx: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DecisionEventCreate(BaseModel):
    company_id: Optional[str] = None
    decision_type: str
    subject_type: str
    subject_id: str
    decision_maker_type: str
    decision_maker_id: str
    rationale: Optional[str] = None
    alternatives: Optional[list] = []
    selected_option: Optional[str] = None
    confidence_score: Optional[str] = "0.0"
    metadata_json: Optional[Dict[str, Any]] = {}
    proof_hash: str


class SettlementEligibilityCreate(BaseModel):
    job_id: Optional[str] = None
    work_order_id: Optional[str] = None
    bounty_id: Optional[str] = None
    recipient_wallet: Optional[str] = None
    recipient_user_id: Optional[str] = None
    eligible_amount: str
    currency: Optional[str] = "USD"
    criteria_met: Optional[list] = []
    proof_hash: str
