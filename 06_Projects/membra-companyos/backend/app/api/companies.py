"""CompanyOS API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.base import get_db
from app.services.company import CompanyService
from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate, DepartmentCreate, SOPCreate, CompanyMemoryCreate, InitiativeCreate, KPIRecordCreate
from app.schemas.common import BaseResponse, PaginatedResponse

router = APIRouter()


@router.post("/", response_model=BaseResponse)
def create_company(data: CompanyCreate, db: Session = Depends(get_db)):
    svc = CompanyService(db)
    company = svc.create_company(data)
    return BaseResponse(data={"id": str(company.id), "slug": company.slug})


@router.get("/", response_model=PaginatedResponse)
def list_companies(limit: int = Query(50, ge=1, le=100), db: Session = Depends(get_db)):
    # Placeholder
    return PaginatedResponse(items=[], total=0, page=1, page_size=limit, pages=0)


@router.get("/{company_id}", response_model=BaseResponse)
def get_company(company_id: str, db: Session = Depends(get_db)):
    svc = CompanyService(db)
    dashboard = svc.get_company_dashboard(company_id)
    return BaseResponse(data=dashboard)


@router.patch("/{company_id}", response_model=BaseResponse)
def update_company(company_id: str, data: CompanyUpdate, db: Session = Depends(get_db)):
    svc = CompanyService(db)
    company = svc.update_company(company_id, data)
    return BaseResponse(data={"id": str(company.id), "status": company.status.value})


@router.post("/{company_id}/departments", response_model=BaseResponse)
def create_department(company_id: str, data: DepartmentCreate, db: Session = Depends(get_db)):
    svc = CompanyService(db)
    data.company_id = company_id
    dept = svc.create_department(data)
    return BaseResponse(data={"id": str(dept.id), "type": dept.dept_type.value})


@router.post("/{company_id}/sops", response_model=BaseResponse)
def create_sop(company_id: str, data: SOPCreate, db: Session = Depends(get_db)):
    svc = CompanyService(db)
    data.company_id = company_id
    sop = svc.create_sop(data)
    return BaseResponse(data={"id": str(sop.id), "version": sop.version})


@router.post("/{company_id}/memories", response_model=BaseResponse)
def add_memory(company_id: str, data: CompanyMemoryCreate, db: Session = Depends(get_db)):
    svc = CompanyService(db)
    data.company_id = company_id
    mem = svc.add_memory(data)
    return BaseResponse(data={"id": str(mem.id), "key": mem.key})


@router.post("/{company_id}/initiatives", response_model=BaseResponse)
def create_initiative(company_id: str, data: InitiativeCreate, db: Session = Depends(get_db)):
    svc = CompanyService(db)
    data.company_id = company_id
    init = svc.create_initiative(data)
    return BaseResponse(data={"id": str(init.id), "status": init.status.value})


@router.post("/{company_id}/kpis", response_model=BaseResponse)
def record_kpi(company_id: str, data: KPIRecordCreate, db: Session = Depends(get_db)):
    svc = CompanyService(db)
    data.company_id = company_id
    kpi = svc.record_kpi(data)
    return BaseResponse(data={"id": str(kpi.id), "value": float(kpi.value)})
