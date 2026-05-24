"""MEMBRA CompanyOS — SettlementOS service."""
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.settlement import SettlementRecord, SettlementStatus, SettlementRail, PayoutInstruction, ExternalRailLog
from app.schemas.settlement import SettlementRecordCreate, PayoutInstructionCreate, ExternalRailLogCreate
from app.core.logging import get_logger
from app.services.proofbook import ProofBookService

logger = get_logger(__name__)


class SettlementService:
    def __init__(self, db: Session):
        self.db = db
        self.proof = ProofBookService(db)

    def create_record(self, data: SettlementRecordCreate) -> SettlementRecord:
        record = SettlementRecord(
            company_id=UUID(data.company_id) if data.company_id else None,
            eligibility_id=UUID(data.eligibility_id) if data.eligibility_id else None,
            job_id=UUID(data.job_id) if data.job_id else None,
            recipient_type=data.recipient_type,
            recipient_id=UUID(data.recipient_id),
            recipient_wallet=data.recipient_wallet,
            amount=data.amount,
            currency=data.currency,
            rail=SettlementRail(data.rail),
            fee_amount=data.fee_amount or 0,
            metadata_json=data.metadata_json or {},
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        self.proof.write_entry(
            entry_type="SETTLEMENT_TRIGGERED",
            resource_type="settlement",
            resource_id=record.id,
            actor_type="system",
            actor_id=UUID("00000000-0000-0000-0000-000000000000"),
            description=f"Settlement triggered: {data.amount} {data.currency} via {data.rail}",
            data={"amount": data.amount, "rail": data.rail, "recipient": data.recipient_wallet},
        )
        return record

    def send_instructions(self, settlement_id: str, instructions: List[PayoutInstructionCreate]) -> SettlementRecord:
        record = self.db.query(SettlementRecord).filter(SettlementRecord.id == UUID(settlement_id)).first()
        if not record:
            raise ValueError("Settlement not found")
        record.status = SettlementStatus.INSTRUCTIONS_SENT
        record.instructions_sent_at = datetime.now(timezone.utc)
        for inst_data in instructions:
            inst = PayoutInstruction(
                settlement_id=record.id,
                instruction_type=inst_data.instruction_type,
                payload=inst_data.payload or {},
                sent_at=datetime.now(timezone.utc),
            )
            self.db.add(inst)
        self.db.commit()
        self.db.refresh(record)
        return record

    def mark_settled(self, settlement_id: str, external_tx_id: Optional[str] = None) -> SettlementRecord:
        record = self.db.query(SettlementRecord).filter(SettlementRecord.id == UUID(settlement_id)).first()
        if not record:
            raise ValueError("Settlement not found")
        record.status = SettlementStatus.SETTLED
        record.settled_at = datetime.now(timezone.utc)
        record.external_tx_id = external_tx_id
        self.db.commit()
        self.db.refresh(record)
        self.proof.write_entry(
            entry_type="EXTERNAL_SETTLEMENT",
            resource_type="settlement",
            resource_id=record.id,
            actor_type="system",
            actor_id=UUID("00000000-0000-0000-0000-000000000000"),
            description=f"Settlement confirmed: {external_tx_id}",
            data={"tx_id": external_tx_id, "status": "settled"},
        )
        return record

    def log_rail_event(self, data: ExternalRailLogCreate) -> ExternalRailLog:
        log = ExternalRailLog(
            settlement_id=UUID(data.settlement_id),
            rail=SettlementRail(data.rail),
            event_type=data.event_type,
            request_payload=data.request_payload or {},
            response_payload=data.response_payload or {},
            status_code=data.status_code,
            error_message=data.error_message,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def list_settlements(self, company_id: Optional[str] = None, status: Optional[str] = None, limit: int = 50) -> List[SettlementRecord]:
        q = self.db.query(SettlementRecord)
        if company_id:
            q = q.filter(SettlementRecord.company_id == UUID(company_id))
        if status:
            q = q.filter(SettlementRecord.status == SettlementStatus(status))
        return q.order_by(SettlementRecord.created_at.desc()).limit(limit).all()
