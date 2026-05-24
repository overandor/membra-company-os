"""Tests for the 60-LLM Employee Workforce System."""
import os
import pytest
from sqlalchemy.orm import Session

os.environ["SECRET_KEY"] = "test-secret-key-must-be-at-least-32-characters-long"
os.environ["DATABASE_URL"] = "sqlite:///./test_workforce.db"

from app.db.base import engine, Base, SessionLocal
from app.services.workforce import WorkforceService
from app.core.workforce_config import EMPLOYEES, DEPARTMENTS
from app.models.workforce import WorkforceEmployee, WorkforceContribution


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_workforce_config_has_60_employees():
    assert len(EMPLOYEES) == 60
    assert len(DEPARTMENTS) == 12


def test_workforce_service_seed(db: Session):
    svc = WorkforceService(db)
    result = svc.ensure_employees()
    assert result["created"] == 60
    assert result["skipped"] == 0
    assert result["total"] == 60

    # Idempotent
    result2 = svc.ensure_employees()
    assert result2["created"] == 0
    assert result2["skipped"] == 60


def test_list_employees(db: Session):
    svc = WorkforceService(db)
    svc.ensure_employees()

    all_emps = svc.list_employees()
    assert len(all_emps) == 60

    strategy = svc.list_employees(department="strategy")
    assert len(strategy) == 5

    engineering = svc.list_employees(department="engineering")
    assert len(engineering) == 8


def test_get_employee(db: Session):
    svc = WorkforceService(db)
    svc.ensure_employees()

    emp = svc.get_employee("strat_01")
    assert emp is not None
    assert emp.name == "Alex Vision"
    assert emp.department == "strategy"
    assert emp.status == "idle"

    missing = svc.get_employee("nonexistent")
    assert missing is None


def test_departments_with_counts(db: Session):
    svc = WorkforceService(db)
    svc.ensure_employees()

    depts = svc.get_departments()
    assert len(depts) == 12

    dept_map = {d["id"]: d for d in depts}
    assert dept_map["strategy"]["employee_count"] == 5
    assert dept_map["engineering"]["employee_count"] == 8
    assert dept_map["operations"]["employee_count"] == 6


def test_stats(db: Session):
    svc = WorkforceService(db)
    svc.ensure_employees()

    stats = svc.get_stats()
    assert stats["total_employees"] == 60
    assert stats["running"] == 0
    assert stats["idle"] == 60
    assert stats["errors"] == 0
    assert stats["total_contributions"] == 0
    assert "departments" in stats


@pytest.mark.asyncio
async def test_run_employee_no_ollama(db: Session):
    """Running an employee without Ollama should record error gracefully."""
    svc = WorkforceService(db)
    svc.ensure_employees()

    result = await svc.run_employee("strat_01", task_prompt="Write a brief status report.")
    # Without ollama running, it should return failure but not crash
    assert "success" in result
    assert "employee_id" in result
    assert result["employee_id"] == "strat_01"

    # Employee status should be updated (either idle if success, error if failure)
    emp = svc.get_employee("strat_01")
    assert emp.total_runs == 1


def test_contributions_empty(db: Session):
    svc = WorkforceService(db)
    svc.ensure_employees()

    contribs = svc.get_contributions()
    assert len(contribs) == 0

    contribs = svc.get_contributions(employee_id="strat_01")
    assert len(contribs) == 0
