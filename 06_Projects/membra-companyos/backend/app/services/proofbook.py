"""MEMBRA CompanyOS — ProofBook service."""
import json
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
import hashlib

from app.models.proofbook import ProofBookEntry, ProofEntryType, ProofChain, DecisionEvent, SettlementEligibility
from app.schemas.proofbook import ProofBookEntryCreate, ProofChainCreate, DecisionEventCreate, SettlementEligibilityCreate
from app.core.logging import get_logger

logger = get_logger(__name__)


def canonical_json(payload: dict) -> str:
    """Deterministic canonical JSON: sorted keys, no extra whitespace."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


class ProofBookService:
    def __init__(self, db: Session):
        self.db = db

    def write_entry(self, entry_type: str, resource_type: str, resource_id: UUID,
                    actor_type: str, actor_id: UUID, description: Optional[str] = None,
                    data: Optional[dict] = None, ipfs_cid: Optional[str] = None,
                    chain_id: Optional[UUID] = None, block_number: Optional[str] = None,
                    tx_hash: Optional[str] = None, company_id: Optional[UUID] = None,
                    source_module: Optional[str] = None, metadata: Optional[dict] = None) -> ProofBookEntry:
        payload = {
            "entry_type": entry_type,
            "resource_type": resource_type,
            "resource_id": str(resource_id),
            "actor_type": actor_type,
            "actor_id": str(actor_id),
            "description": description or "",
            "data": data or {},
            "ipfs_cid": ipfs_cid or "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_module": source_module or "",
            "metadata": metadata or {},
        }
        proof_hash = hashlib.sha3_256(canonical_json(payload).encode()).hexdigest()

        previous_hash = None
        if chain_id:
            chain = self.db.query(ProofChain).filter(ProofChain.id == chain_id).first()
            if chain:
                previous_hash = chain.latest_hash
                chain.latest_hash = proof_hash
                chain.entry_count = str(int(chain.entry_count) + 1)
        else:
            last_entry = self.db.query(ProofBookEntry).filter(
                ProofBookEntry.resource_type == resource_type,
                ProofBookEntry.resource_id == resource_id
            ).order_by(ProofBookEntry.created_at.desc()).first()
            if last_entry:
                previous_hash = last_entry.proof_hash

        entry = ProofBookEntry(
            entry_type=ProofEntryType(entry_type) if entry_type in [e.value for e in ProofEntryType] else ProofEntryType.TASK_CREATED,
            company_id=company_id,
            resource_type=resource_type,
            resource_id=resource_id,
            actor_type=actor_type,
            actor_id=actor_id,
            description=description,
            data=data or {},
            ipfs_cid=ipfs_cid,
            proof_hash=proof_hash,
            previous_hash=previous_hash,
            chain_id=chain_id,
            block_number=block_number,
            tx_hash=tx_hash,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def create_chain(self, data: ProofChainCreate) -> ProofChain:
        chain = ProofChain(
            company_id=UUID(data.company_id) if data.company_id else None,
            chain_name=data.chain_name,
            chain_type=data.chain_type,
            genesis_hash=data.genesis_hash,
            latest_hash=data.latest_hash,
            anchored_to=data.anchored_to,
        )
        self.db.add(chain)
        self.db.commit()
        self.db.refresh(chain)
        return chain

    def get_chain(self, chain_id: str) -> Optional[ProofChain]:
        return self.db.query(ProofChain).filter(ProofChain.id == UUID(chain_id)).first()

    def get_entries_for_resource(self, resource_type: str, resource_id: str, limit: int = 50) -> List[ProofBookEntry]:
        return self.db.query(ProofBookEntry).filter(
            ProofBookEntry.resource_type == resource_type,
            ProofBookEntry.resource_id == UUID(resource_id)
        ).order_by(ProofBookEntry.created_at.desc()).limit(limit).all()

    def verify_chain_integrity(self, chain_id: str) -> dict:
        chain = self.get_chain(chain_id)
        if not chain:
            return {"valid": False, "error": "Chain not found"}
        entries = self.db.query(ProofBookEntry).filter(
            ProofBookEntry.chain_id == UUID(chain_id)
        ).order_by(ProofBookEntry.created_at).all()
        for i, entry in enumerate(entries):
            entry_data = {
                "entry_type": entry.entry_type.value if entry.entry_type else "",
                "resource_type": entry.resource_type,
                "resource_id": str(entry.resource_id),
                "actor_type": entry.actor_type,
                "actor_id": str(entry.actor_id),
                "description": entry.description or "",
                "data": entry.data or {},
                "ipfs_cid": entry.ipfs_cid or "",
                "timestamp": entry.created_at.isoformat() if entry.created_at else "",
                "source_module": "",
                "metadata": {},
            }
            computed = hashlib.sha3_256(canonical_json(entry_data).encode()).hexdigest()
            if computed != entry.proof_hash:
                return {"valid": False, "error": f"Hash mismatch at entry {i}", "entry_id": str(entry.id)}
        return {"valid": True, "entry_count": len(entries), "chain_id": chain_id}

    def record_decision(self, data: DecisionEventCreate) -> DecisionEvent:
        event = DecisionEvent(
            company_id=UUID(data.company_id) if data.company_id else None,
            decision_type=data.decision_type,
            subject_type=data.subject_type,
            subject_id=UUID(data.subject_id),
            decision_maker_type=data.decision_maker_type,
            decision_maker_id=UUID(data.decision_maker_id),
            rationale=data.rationale,
            alternatives=data.alternatives or [],
            selected_option=data.selected_option,
            confidence_score=data.confidence_score,
            metadata_json=data.metadata_json or {},
            proof_hash=data.proof_hash,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def create_eligibility(self, data: SettlementEligibilityCreate) -> SettlementEligibility:
        elig = SettlementEligibility(
            job_id=UUID(data.job_id) if data.job_id else None,
            work_order_id=UUID(data.work_order_id) if data.work_order_id else None,
            bounty_id=UUID(data.bounty_id) if data.bounty_id else None,
            recipient_wallet=data.recipient_wallet,
            recipient_user_id=UUID(data.recipient_user_id) if data.recipient_user_id else None,
            eligible_amount=data.eligible_amount,
            currency=data.currency,
            criteria_met=data.criteria_met or [],
            proof_hash=data.proof_hash,
        )
        self.db.add(elig)
        self.db.commit()
        self.db.refresh(elig)
        return elig
