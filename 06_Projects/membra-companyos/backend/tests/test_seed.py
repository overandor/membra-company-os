"""Test seed script creates company and agents."""
import os
os.environ.setdefault("SECRET_KEY", "test-secret-key-must-be-at-least-32-characters-long")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_seed.db")

from app.db.base import SessionLocal, engine, Base
from app.models.company import Company
from app.models.agent import Agent
from seed import seed


def test_seed_creates_company():
    Base.metadata.create_all(bind=engine)
    seed()
    db = SessionLocal()
    try:
        company = db.query(Company).filter(Company.slug == "membra-demo").first()
        assert company is not None
        assert company.name == "MEMBRA Demo Unit"
    finally:
        db.close()


def test_seed_creates_agents():
    db = SessionLocal()
    try:
        agents = db.query(Agent).all()
        assert len(agents) >= 10
    finally:
        db.close()
