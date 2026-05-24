"""MEMBRA CompanyOS — CompanyOS service."""
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.company import Company, CompanyStatus, Department, DepartmentType, SOP, CompanyMemory, Initiative, InitiativeStatus, KPIRecord
from app.schemas.company import CompanyCreate, CompanyUpdate, DepartmentCreate, SOPCreate, CompanyMemoryCreate, InitiativeCreate, KPIRecordCreate
from app.core.logging import get_logger
from app.services.proofbook import ProofBookService

logger = get_logger(__name__)


class CompanyService:
    def __init__(self, db: Session):
        self.db = db
        self.proof = ProofBookService(db)

    def create_company(self, data: CompanyCreate) -> Company:
        company = Company(
            name=data.name,
            slug=data.slug,
            description=data.description,
            currency=data.currency,
            owner_wallet=data.owner_wallet,
            metadata_json=data.metadata_json or {},
        )
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        self.proof.write_entry(
            entry_type="TASK_CREATED",
            resource_type="company",
            resource_id=company.id,
            actor_type="system",
            actor_id=UUID("00000000-0000-0000-0000-000000000000"),
            description=f"Company created: {data.name}",
            data={"slug": data.slug, "owner": data.owner_wallet},
        )
        return company

    def update_company(self, company_id: str, data: CompanyUpdate) -> Company:
        company = self.db.query(Company).filter(Company.id == UUID(company_id)).first()
        if not company:
            raise ValueError("Company not found")
        for field, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(company, field, value)
        self.db.commit()
        self.db.refresh(company)
        return company

    def create_department(self, data: DepartmentCreate) -> Department:
        dept = Department(
            company_id=UUID(data.company_id),
            name=data.name,
            dept_type=DepartmentType(data.dept_type),
            description=data.description,
            lead_agent_id=UUID(data.lead_agent_id) if data.lead_agent_id else None,
            kpi_json=data.kpi_json or {},
        )
        self.db.add(dept)
        self.db.commit()
        self.db.refresh(dept)
        return dept

    def create_sop(self, data: SOPCreate) -> SOP:
        sop = SOP(
            company_id=UUID(data.company_id),
            department_id=UUID(data.department_id) if data.department_id else None,
            title=data.title,
            version=data.version,
            content=data.content,
            steps=data.steps or [],
            triggers=data.triggers or [],
            output_schema=data.output_schema or {},
        )
        self.db.add(sop)
        self.db.commit()
        self.db.refresh(sop)
        return sop

    def add_memory(self, data: CompanyMemoryCreate) -> CompanyMemory:
        mem = CompanyMemory(
            company_id=UUID(data.company_id),
            memory_type=data.memory_type,
            key=data.key,
            value=data.value or {},
            importance_score=data.importance_score or 0.0,
            source_agent_id=UUID(data.source_agent_id) if data.source_agent_id else None,
        )
        self.db.add(mem)
        self.db.commit()
        self.db.refresh(mem)
        return mem

    def create_initiative(self, data: InitiativeCreate) -> Initiative:
        init = Initiative(
            company_id=UUID(data.company_id),
            title=data.title,
            description=data.description,
            priority=data.priority,
            target_kpi_json=data.target_kpi_json or {},
        )
        self.db.add(init)
        self.db.commit()
        self.db.refresh(init)
        return init

    def record_kpi(self, data: KPIRecordCreate) -> KPIRecord:
        kpi = KPIRecord(
            company_id=UUID(data.company_id),
            kpi_name=data.kpi_name,
            kpi_category=data.kpi_category,
            value=data.value,
            unit=data.unit,
            period_start=data.period_start,
            period_end=data.period_end,
            source=data.source,
        )
        self.db.add(kpi)
        self.db.commit()
        self.db.refresh(kpi)
        self.proof.write_entry(
            entry_type="KPI_RECORDED",
            resource_type="kpi",
            resource_id=kpi.id,
            actor_type="system",
            actor_id=UUID("00000000-0000-0000-0000-000000000000"),
            description=f"KPI recorded: {data.kpi_name} = {data.value}",
            data={"category": data.kpi_category, "value": data.value, "unit": data.unit},
        )
        return kpi

    def get_company_dashboard(self, company_id: str) -> dict:
        company = self.db.query(Company).filter(Company.id == UUID(company_id)).first()
        if not company:
            raise ValueError("Company not found")
        return {
            "company": {"id": str(company.id), "name": company.name, "status": company.status.value},
            "departments": len(company.departments),
            "sops": len(company.sops),
            "initiatives": {
                "total": len(company.initiatives),
                "active": sum(1 for i in company.initiatives if i.status == InitiativeStatus.ACTIVE),
            },
            "kpi_count": len(company.kpi_records),
            "memory_count": len(company.memories),
            "member_count": len(company.members),
        }
