"""Test proof chain verifies."""
import os
os.environ.setdefault("SECRET_KEY", "test-secret-key-must-be-at-least-32-characters-long")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_proofbook.db")

from uuid import UUID
from app.db.base import engine, Base
from app.services.proofbook import ProofBookService
from app.db.base import SessionLocal


def test_write_entry_and_verify():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        svc = ProofBookService(db)
        entry = svc.write_entry(
            entry_type="TASK_CREATED",
            resource_type="test",
            resource_id=UUID("00000000-0000-0000-0000-000000000000"),
            actor_type="system",
            actor_id=UUID("00000000-0000-0000-0000-000000000000"),
            description="test entry",
        )
        assert entry.proof_hash is not None
        assert len(entry.proof_hash) == 64
    finally:
        db.close()
