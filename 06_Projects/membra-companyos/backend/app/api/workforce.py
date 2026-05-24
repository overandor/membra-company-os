"""MEMBRA CompanyOS — Workforce API for 60 LLM employees."""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.services.workforce import WorkforceService
from app.core.workforce_config import EMPLOYEES, DEPARTMENTS

router = APIRouter(prefix="/workforce", tags=["Workforce"])


class EmployeeRunRequest(BaseModel):
    task_prompt: Optional[str] = None


class EmployeeResponse(BaseModel):
    id: str
    employee_id: str
    name: str
    department: str
    title: str
    model: str
    status: str
    responsibilities: List[str]
    total_runs: int
    total_contributions: int
    last_run_at: Optional[str] = None
    last_output: Optional[str] = None
    last_error: Optional[str] = None


class DepartmentResponse(BaseModel):
    id: str
    name: str
    mission: str
    employee_count: int
    active_count: int


class ContributionResponse(BaseModel):
    id: str
    employee_id: str
    department: str
    task_type: str
    output_summary: Optional[str] = None
    duration_ms: Optional[int] = None
    created_at: str


class WorkforceStatsResponse(BaseModel):
    total_employees: int
    running: int
    idle: int
    errors: int
    total_contributions: int
    departments: Dict[str, Any]


@router.post("/seed", response_model=Dict[str, Any])
def seed_workforce(db: Session = Depends(get_db)):
    """Idempotently register all 60 employees from config."""
    svc = WorkforceService(db)
    result = svc.ensure_employees()
    return {"status": "success", "data": result}


@router.get("/employees", response_model=List[EmployeeResponse])
def list_employees(
    department: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
):
    svc = WorkforceService(db)
    items = svc.list_employees(department=department, status=status, limit=limit)
    return [
        EmployeeResponse(
            id=str(e.id),
            employee_id=e.employee_id,
            name=e.name,
            department=e.department,
            title=e.title,
            model=e.model,
            status=e.status,
            responsibilities=e.responsibilities or [],
            total_runs=e.total_runs,
            total_contributions=e.total_contributions,
            last_run_at=e.last_run_at.isoformat() if e.last_run_at else None,
            last_output=e.last_output,
            last_error=e.last_error,
        )
        for e in items
    ]


@router.get("/employees/{employee_id}", response_model=EmployeeResponse)
def get_employee(employee_id: str, db: Session = Depends(get_db)):
    svc = WorkforceService(db)
    e = svc.get_employee(employee_id)
    if not e:
        raise HTTPException(status_code=404, detail="Employee not found")
    return EmployeeResponse(
        id=str(e.id),
        employee_id=e.employee_id,
        name=e.name,
        department=e.department,
        title=e.title,
        model=e.model,
        status=e.status,
        responsibilities=e.responsibilities or [],
        total_runs=e.total_runs,
        total_contributions=e.total_contributions,
        last_run_at=e.last_run_at.isoformat() if e.last_run_at else None,
        last_output=e.last_output,
        last_error=e.last_error,
    )


@router.post("/employees/{employee_id}/run", response_model=Dict[str, Any])
async def run_employee(
    employee_id: str,
    data: EmployeeRunRequest,
    db: Session = Depends(get_db),
):
    """Execute a task via the employee's Ollama connector."""
    svc = WorkforceService(db)
    result = await svc.run_employee(employee_id, task_prompt=data.task_prompt)
    if not result.get("success") and result.get("error") == "Employee not found":
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"status": "success" if result.get("success") else "error", "data": result}


@router.get("/departments", response_model=List[DepartmentResponse])
def list_departments(db: Session = Depends(get_db)):
    svc = WorkforceService(db)
    return svc.get_departments()


@router.get("/contributions", response_model=List[ContributionResponse])
def list_contributions(
    employee_id: Optional[str] = None,
    department: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    svc = WorkforceService(db)
    items = svc.get_contributions(employee_id=employee_id, department=department, limit=limit)
    return [
        ContributionResponse(
            id=str(c.id),
            employee_id=c.employee_id,
            department=c.department,
            task_type=c.task_type,
            output_summary=c.output_summary,
            duration_ms=c.duration_ms,
            created_at=c.created_at.isoformat() if c.created_at else None,
        )
        for c in items
    ]


@router.get("/stats", response_model=WorkforceStatsResponse)
def get_stats(db: Session = Depends(get_db)):
    svc = WorkforceService(db)
    return svc.get_stats()


@router.get("/config/employees")
def get_config_employees():
    """Return the raw 60-employee configuration."""
    return {"status": "success", "data": EMPLOYEES}


@router.get("/config/departments")
def get_config_departments():
    """Return the department configuration."""
    return {"status": "success", "data": DEPARTMENTS}
