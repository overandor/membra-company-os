"""Test that all app modules import cleanly."""
import os
os.environ.setdefault("SECRET_KEY", "test-secret-key-must-be-at-least-32-characters-long")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_imports.db")


def test_main_app_import():
    from app.main import app
    assert app is not None


def test_models_import():
    from app.models import (
        Base, Company, Department, SOP, CompanyMemory, Initiative, KPIRecord,
        Intent, Objective, ObjectiveTaskLink,
        Task, TaskDependency, TaskAssignment, TaskProof,
        Agent, AgentTool, AgentActionLog,
        Job, Bounty, WorkOrder, MarketplaceAction, JobProof,
        ApprovalGate, Policy, ConsentRecord, RiskClassification, EscalationRule,
        ProofBookEntry, ProofChain, DecisionEvent, SettlementEligibility,
        SettlementRecord, PayoutInstruction, ExternalRailLog,
        WorldAsset, AssetListing, AssetReservation, AssetProof, Vendor, Person, Route,
        User, UserRole, Session, AuditLog,
    )


def test_services_import():
    from app.services import (
        agent, auth, company, governance, intent, job, llm_concierge,
        orchestration, proofbook, settlement, task, worldbridge,
    )


def test_schemas_import():
    from app.schemas import (
        agent, company, governance, intent, job, proofbook, settlement,
        task, user, worldbridge, common,
    )
