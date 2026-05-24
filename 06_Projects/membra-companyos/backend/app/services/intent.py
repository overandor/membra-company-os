"""MEMBRA CompanyOS — IntentOS service."""
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.intent import Intent, IntentStatus, Objective, ObjectiveStatus, ObjectiveTaskLink
from app.schemas.intent import IntentCreate, IntentUpdate, ObjectiveCreate
from app.core.logging import get_logger
from app.services.proofbook import ProofBookService

logger = get_logger(__name__)


class IntentService:
    def __init__(self, db: Session):
        self.db = db
        self.proof = ProofBookService(db)

    def create_intent(self, data: IntentCreate) -> Intent:
        intent = Intent(
            raw_text=data.raw_text,
            user_wallet=data.user_wallet,
            user_id=UUID(data.user_id) if data.user_id else None,
            status=IntentStatus.RAW,
            metadata_json=data.metadata_json or {},
        )
        self.db.add(intent)
        self.db.commit()
        self.db.refresh(intent)
        self.proof.write_entry(
            entry_type="TASK_CREATED",
            resource_type="intent",
            resource_id=intent.id,
            actor_type="human",
            actor_id=intent.user_id or UUID("00000000-0000-0000-0000-000000000000"),
            description=f"Intent created: {data.raw_text[:100]}",
            data={"raw_text": data.raw_text},
        )
        return intent

    def parse_intent(self, intent_id: str, parsed: dict) -> Intent:
        intent = self.db.query(Intent).filter(Intent.id == UUID(intent_id)).first()
        if not intent:
            raise ValueError("Intent not found")
        intent.parsed_json = parsed
        intent.status = IntentStatus.PARSED
        self.db.commit()
        self.db.refresh(intent)
        return intent

    def structure_objectives(self, intent_id: str, objectives_data: List[dict]) -> List[Objective]:
        intent = self.db.query(Intent).filter(Intent.id == UUID(intent_id)).first()
        if not intent:
            raise ValueError("Intent not found")
        objs = []
        for obj_data in objectives_data:
            obj = Objective(
                intent_id=intent.id,
                title=obj_data.get("title", "Untitled Objective"),
                description=obj_data.get("description"),
                priority=obj_data.get("priority", "medium"),
                success_criteria=obj_data.get("success_criteria", []),
                assigned_department=obj_data.get("assigned_department"),
                metadata_json=obj_data.get("metadata", {}),
            )
            self.db.add(obj)
            objs.append(obj)
        intent.status = IntentStatus.OBJECTIVES_CREATED
        self.db.commit()
        for obj in objs:
            self.db.refresh(obj)
        return objs

    def list_intents(self, user_id: Optional[str] = None, status: Optional[str] = None, limit: int = 50) -> List[Intent]:
        q = self.db.query(Intent)
        if user_id:
            q = q.filter(Intent.user_id == UUID(user_id))
        if status:
            q = q.filter(Intent.status == IntentStatus(status))
        return q.order_by(Intent.created_at.desc()).limit(limit).all()
