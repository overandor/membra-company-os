"""MEMBRA CompanyOS — Seed script for demo data."""
import os
os.environ.setdefault("SECRET_KEY", "seed-secret-key-256-bit-membra-companyos-seed-only")
os.environ.setdefault("DATABASE_URL", "sqlite:///./membra_seed.db")

from app.db.base import SessionLocal, engine, Base
from app.models.company import Company, CompanyStatus, Department, DepartmentType
from app.models.agent import Agent, AgentType, AgentStatus
from app.models.worldbridge import WorldAsset, AssetType, AssetStatus
from app.models.task import Task, TaskStatus, TaskType
from app.models.job import Job, JobType, JobStatus
from app.models.governance import ApprovalGate, RiskLevel
from app.models.proofbook import ProofBookEntry, ProofEntryType
from app.models.company import KPIRecord
from app.core.security import hash_proof


def seed():
    Base.metadata.create_all(bind=engine)
    print("Tables created.")
    db = SessionLocal()
    try:
        # Idempotent: check if company already exists
        existing = db.query(Company).filter(Company.slug == "membra-demo").first()
        if existing:
            print(f"Company already exists: {existing.name} ({existing.id})")
            company = existing
        else:
            company = Company(
                name="MEMBRA Demo Unit",
                slug="membra-demo",
                description="Autonomous company orchestration demonstration",
                status=CompanyStatus.ACTIVE,
                owner_wallet="0x0000000000000000000000000000000000000000",
            )
            db.add(company)
            db.commit()
            db.refresh(company)
            print(f"Created company: {company.name} ({company.id})")

        # Create departments
        depts = [
            Department(company_id=company.id, name="Strategy", dept_type=DepartmentType.STRATEGY),
            Department(company_id=company.id, name="Product", dept_type=DepartmentType.PRODUCT),
            Department(company_id=company.id, name="Engineering", dept_type=DepartmentType.ENGINEERING),
            Department(company_id=company.id, name="Operations", dept_type=DepartmentType.OPERATIONS),
            Department(company_id=company.id, name="Sales", dept_type=DepartmentType.SALES),
            Department(company_id=company.id, name="Finance", dept_type=DepartmentType.FINANCE),
            Department(company_id=company.id, name="Legal/Risk", dept_type=DepartmentType.LEGAL_RISK),
            Department(company_id=company.id, name="Governance", dept_type=DepartmentType.GOVERNANCE),
            Department(company_id=company.id, name="Proof", dept_type=DepartmentType.PROOF),
            Department(company_id=company.id, name="Concierge", dept_type=DepartmentType.CONCIERGE),
        ]
        for d in depts:
            db.add(d)
        db.commit()
        print(f"Created {len(depts)} departments")

        # Create agents
        agents = [
            Agent(agent_type=AgentType.STRATEGY, name="Strategy Agent", description="Decides what to build next", allowed_actions=["analyze", "recommend"]),
            Agent(agent_type=AgentType.PRODUCT, name="Product Agent", description="Converts strategy into requirements", allowed_actions=["spec", "design"]),
            Agent(agent_type=AgentType.ENGINEERING, name="Engineering Agent", description="Builds and deploys", allowed_actions=["code", "deploy", "test"]),
            Agent(agent_type=AgentType.OPERATIONS, name="Ops Agent", description="Creates SOPs and flows", allowed_actions=["sop", "schedule"]),
            Agent(agent_type=AgentType.SALES, name="Sales Agent", description="Generates offers and outreach", allowed_actions=["offer", "outreach"]),
            Agent(agent_type=AgentType.FINANCE, name="Finance Agent", description="Tracks unit economics", allowed_actions=["forecast", "report"]),
            Agent(agent_type=AgentType.LEGAL_RISK, name="Legal/Risk Agent", description="Flags risks", allowed_actions=["review", "flag"]),
            Agent(agent_type=AgentType.GOVERNANCE, name="Governance Agent", description="Controls approvals", allowed_actions=["approve", "escalate"]),
            Agent(agent_type=AgentType.PROOF, name="Proof Agent", description="Writes to ProofBook", allowed_actions=["hash", "verify"]),
            Agent(agent_type=AgentType.CONCIERGE, name="Concierge Agent", description="Front-facing LLM", allowed_actions=["chat", "orchestrate"]),
        ]
        for a in agents:
            db.add(a)
        db.commit()
        print(f"Created {len(agents)} agents")

        # Create world assets
        assets = [
            WorldAsset(owner_wallet="0xDemoWallet1", asset_type=AssetType.WINDOW, name="First Floor Window", location_json={"address": "123 Main St"}),
            WorldAsset(owner_wallet="0xDemoWallet1", asset_type=AssetType.VEHICLE, name="Delivery Van", location_json={"address": "123 Main St"}),
            WorldAsset(owner_wallet="0xDemoWallet2", asset_type=AssetType.APARTMENT, name="Studio Apartment", location_json={"address": "456 Oak Ave"}),
            WorldAsset(owner_wallet="0xDemoWallet2", asset_type=AssetType.TOOL, name="Power Drill", location_json={"address": "456 Oak Ave"}),
        ]
        for a in assets:
            db.add(a)
        db.commit()
        print(f"Created {len(assets)} world assets")

        # Create tasks
        tasks = [
            Task(title="Inventory physical assets", task_type=TaskType.PROOF_COLLECTION, status=TaskStatus.COMPLETED, priority=1),
            Task(title="Register assets in WorldBridge", task_type=TaskType.ASSET_DEPLOYMENT, status=TaskStatus.IN_PROGRESS, priority=2),
            Task(title="Draft marketplace listings", task_type=TaskType.AI_ANALYSIS, status=TaskStatus.TODO, priority=1),
            Task(title="Obtain owner consent", task_type=TaskType.GOVERNANCE_GATE, status=TaskStatus.BLOCKED, priority=2, blocked_reason="Awaiting wallet signature"),
        ]
        for t in tasks:
            db.add(t)
        db.commit()
        print(f"Created {len(tasks)} tasks")

        # Create jobs
        jobs = [
            Job(title="Window Ad Campaign Setup", job_type=JobType.WINDOW_AD_TASK, status=JobStatus.POSTED, budget=100, currency="USD"),
            Job(title="Vehicle Wrap Installation", job_type=JobType.CAR_AD_TASK, status=JobStatus.ASSIGNED, budget=250, currency="USD"),
            Job(title="Local Delivery Route", job_type=JobType.FULFILLMENT, status=JobStatus.IN_PROGRESS, budget=50, currency="USD"),
        ]
        for j in jobs:
            db.add(j)
        db.commit()
        print(f"Created {len(jobs)} jobs")

        # Create governance gates
        gates = [
            ApprovalGate(gate_type="owner_consent", resource_type="asset_listing", resource_id=assets[0].id, risk_level=RiskLevel.MEDIUM),
            ApprovalGate(gate_type="owner_consent", resource_type="asset_listing", resource_id=assets[1].id, risk_level=RiskLevel.LOW),
        ]
        for g in gates:
            db.add(g)
        db.commit()
        print(f"Created {len(gates)} governance gates")

        # Create ProofBook entries
        proof = ProofBookEntry(
            entry_type=ProofEntryType.TASK_CREATED,
            resource_type="orchestration",
            resource_id=company.id,
            actor_type="system",
            actor_id=company.id,
            description="Initial seed data loaded",
            proof_hash=hash_proof("seed-data-initial-load"),
        )
        db.add(proof)
        db.commit()
        print(f"Created proofbook entry: {proof.proof_hash[:16]}...")

        # Create KPIs
        kpis = [
            KPIRecord(company_id=company.id, kpi_name="active_assets", kpi_category="worldbridge", value=4, unit="count", period_start=company.created_at, period_end=company.created_at),
            KPIRecord(company_id=company.id, kpi_name="active_tasks", kpi_category="taskos", value=4, unit="count", period_start=company.created_at, period_end=company.created_at),
            KPIRecord(company_id=company.id, kpi_name="registered_agents", kpi_category="agentos", value=10, unit="count", period_start=company.created_at, period_end=company.created_at),
        ]
        for k in kpis:
            db.add(k)
        db.commit()
        print(f"Created {len(kpis)} KPI records")

        print("\nSeed complete. Dashboard data ready.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
