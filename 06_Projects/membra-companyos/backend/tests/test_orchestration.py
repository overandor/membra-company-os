"""Test orchestration creates tasks/jobs/gates/proofs from intent text."""
import os
os.environ.setdefault("SECRET_KEY", "test-secret-key-must-be-at-least-32-characters-long")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_orchestrate.db")

from app.db.base import engine, Base
from app.services.orchestration import OrchestrationService
from app.db.base import SessionLocal


def test_orchestrate_creates_tasks_and_jobs():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        svc = OrchestrationService(db)
        result = svc.orchestrate("I have a car and a window to rent out")
        assert "intent_id" in result
        assert "objectives" in result
        assert "tasks" in result
        assert "jobs" in result
        assert "gates" in result
        assert "proof_hash" in result
        assert len(result["tasks"]) > 0
    finally:
        db.close()
