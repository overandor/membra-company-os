"""MEMBRA CompanyOS — GovernanceOS service."""
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.governance import (
    ApprovalGate, ApprovalStatus, Policy, PolicyStatus, ConsentRecord,
    ConsentType, RiskClassification, RiskLevel, EscalationRule
)
from app.schemas.governance import (
    ApprovalGateCreate, PolicyCreate, ConsentRecordCreate,
    RiskClassificationCreate, EscalationRuleCreate
)
from app.core.logging import get_logger
from app.services.proofbook import ProofBookService

logger = get_logger(__name__)


class GovernanceService:
    def __init__(self, db: Session):
        self.db = db
        self.proof = ProofBookService(db)

    def create_gate(self, data: ApprovalGateCreate) -> ApprovalGate:
        gate = ApprovalGate(
            gate_type=data.gate_type,
            resource_type=data.resource_type,
            resource_id=UUID(data.resource_id),
            requester_id=UUID(data.requester_id) if data.requester_id else None,
            requester_agent_id=UUID(data.requester_agent_id) if data.requester_agent_id else None,
            risk_level=RiskLevel(data.risk_level) if data.risk_level else RiskLevel.LOW,
            approvers=data.approvers or [],
            required_approvals=data.required_approvals or 1,
            auto_expire_hours=data.auto_expire_hours or 48,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=data.auto_expire_hours or 48),
            metadata_json=data.metadata_json or {},
        )
        self.db.add(gate)
        self.db.commit()
        self.db.refresh(gate)
        self.proof.write_entry(
            entry_type="TASK_CREATED",
            resource_type="approval_gate",
            resource_id=gate.id,
            actor_type="system",
            actor_id=gate.requester_id or UUID("00000000-0000-0000-0000-000000000000"),
            description=f"Approval gate created: {data.gate_type}",
            data={"resource_type": data.resource_type, "risk": data.risk_level},
        )
        return gate

    def approve(self, gate_id: str, approver_id: str, notes: Optional[str] = None) -> ApprovalGate:
        gate = self.db.query(ApprovalGate).filter(ApprovalGate.id == UUID(gate_id)).first()
        if not gate:
            raise ValueError("Gate not found")
        if gate.status != ApprovalStatus.PENDING:
            raise ValueError(f"Gate is {gate.status.value}")
        gate.current_approvals += 1
        if gate.current_approvals >= gate.required_approvals:
            gate.status = ApprovalStatus.APPROVED
            gate.resolved_at = datetime.now(timezone.utc)
        if notes:
            gate.decision_notes = notes
        self.db.commit()
        self.db.refresh(gate)
        self.proof.write_entry(
            entry_type="APPROVAL_GRANTED",
            resource_type="approval_gate",
            resource_id=gate.id,
            actor_type="human",
            actor_id=UUID(approver_id),
            description=f"Gate {gate_id} approved by {approver_id}",
            data={"notes": notes, "current_approvals": gate.current_approvals},
        )
        return gate

    def reject(self, gate_id: str, approver_id: str, notes: Optional[str] = None) -> ApprovalGate:
        gate = self.db.query(ApprovalGate).filter(ApprovalGate.id == UUID(gate_id)).first()
        if not gate:
            raise ValueError("Gate not found")
        gate.rejections += 1
        gate.status = ApprovalStatus.REJECTED
        gate.resolved_at = datetime.now(timezone.utc)
        if notes:
            gate.decision_notes = notes
        self.db.commit()
        self.db.refresh(gate)
        self.proof.write_entry(
            entry_type="APPROVAL_REJECTED",
            resource_type="approval_gate",
            resource_id=gate.id,
            actor_type="human",
            actor_id=UUID(approver_id),
            description=f"Gate {gate_id} rejected by {approver_id}",
            data={"notes": notes},
        )
        return gate

    def create_policy(self, data: PolicyCreate) -> Policy:
        policy = Policy(
            company_id=UUID(data.company_id) if data.company_id else None,
            name=data.name,
            version=data.version,
            policy_type=data.policy_type,
            content=data.content,
            rules=data.rules or [],
            applies_to=data.applies_to or [],
            enforcement_mode=data.enforcement_mode or "audit",
            effective_date=data.effective_date,
            created_by=UUID(data.created_by) if data.created_by else None,
        )
        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)
        return policy

    def record_consent(self, data: ConsentRecordCreate) -> ConsentRecord:
        consent = ConsentRecord(
            consent_type=ConsentType(data.consent_type),
            owner_wallet=data.owner_wallet,
            resource_type=data.resource_type,
            resource_id=UUID(data.resource_id),
            granted=data.granted,
            granted_by=UUID(data.granted_by) if data.granted_by else None,
            granted_at=datetime.now(timezone.utc) if data.granted else None,
            metadata_json=data.metadata_json or {},
        )
        self.db.add(consent)
        self.db.commit()
        self.db.refresh(consent)
        self.proof.write_entry(
            entry_type="CONSENT_GRANTED" if data.granted else "CONSENT_REVOKED",
            resource_type="consent",
            resource_id=consent.id,
            actor_type="human",
            actor_id=UUID(data.granted_by) if data.granted_by else UUID("00000000-0000-0000-0000-000000000000"),
            description=f"Consent {data.consent_type} for {data.resource_type}",
            data={"granted": data.granted, "owner": data.owner_wallet},
        )
        return consent

    def classify_risk(self, data: RiskClassificationCreate) -> RiskClassification:
        risk = RiskClassification(
            resource_type=data.resource_type,
            resource_id=UUID(data.resource_id),
            risk_type=data.risk_type,
            risk_level=RiskLevel(data.risk_level),
            description=data.description,
            mitigation=data.mitigation,
            flagged_by=UUID(data.flagged_by) if data.flagged_by else None,
            flagged_agent_id=UUID(data.flagged_agent_id) if data.flagged_agent_id else None,
        )
        self.db.add(risk)
        self.db.commit()
        self.db.refresh(risk)
        return risk

    def create_escalation_rule(self, data: EscalationRuleCreate) -> EscalationRule:
        rule = EscalationRule(
            company_id=UUID(data.company_id) if data.company_id else None,
            name=data.name,
            trigger_condition=data.trigger_condition,
            trigger_rules=data.trigger_rules or [],
            escalation_path=data.escalation_path or [],
            notify_wallets=data.notify_wallets or [],
            auto_action=data.auto_action,
            is_active=data.is_active if data.is_active is not None else True,
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        self.proof.write_entry(
            entry_type="POLICY_APPLIED",
            resource_type="escalation_rule",
            resource_id=rule.id,
            actor_type="system",
            actor_id=UUID("00000000-0000-0000-0000-000000000000"),
            description=f"Escalation rule created: {data.name}",
            data={"trigger": data.trigger_condition, "auto_action": data.auto_action},
        )
        return rule

    def list_gates(self, status: Optional[str] = None, limit: int = 50) -> List[ApprovalGate]:
        q = self.db.query(ApprovalGate)
        if status:
            q = q.filter(ApprovalGate.status == ApprovalStatus(status))
        return q.order_by(ApprovalGate.created_at.desc()).limit(limit).all()
