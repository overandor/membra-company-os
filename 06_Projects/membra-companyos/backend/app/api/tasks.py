"""TaskOS API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.base import get_db
from app.services.task import TaskService
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate, TaskDependencyCreate, TaskAssignmentCreate, TaskProofCreate
from app.schemas.common import BaseResponse, PaginatedResponse

router = APIRouter()


@router.post("/", response_model=BaseResponse)
def create_task(data: TaskCreate, db: Session = Depends(get_db)):
    svc = TaskService(db)
    task = svc.create_task(data)
    return BaseResponse(data={"id": str(task.id), "status": task.status.value})


@router.get("/", response_model=PaginatedResponse)
def list_tasks(
    company_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    svc = TaskService(db)
    items = svc.list_tasks(company_id=company_id, status=status, limit=limit)
    return PaginatedResponse(
        items=[TaskRead.model_validate(t) for t in items],
        total=len(items),
        page=1,
        page_size=limit,
        pages=1,
    )


@router.patch("/{task_id}", response_model=BaseResponse)
def update_task(task_id: str, data: TaskUpdate, db: Session = Depends(get_db)):
    svc = TaskService(db)
    task = svc.update_status(task_id, data.status or "backlog")
    return BaseResponse(data={"id": str(task.id), "status": task.status.value})


@router.post("/{task_id}/status", response_model=BaseResponse)
def set_status(task_id: str, status: str, reason: Optional[str] = None, db: Session = Depends(get_db)):
    svc = TaskService(db)
    task = svc.update_status(task_id, status, reason)
    return BaseResponse(data={"id": str(task.id), "status": task.status.value})


@router.post("/dependencies", response_model=BaseResponse)
def add_dependency(data: TaskDependencyCreate, db: Session = Depends(get_db)):
    svc = TaskService(db)
    dep = svc.add_dependency(data)
    return BaseResponse(data={"id": str(dep.id)})


@router.post("/assignments", response_model=BaseResponse)
def assign_task(data: TaskAssignmentCreate, db: Session = Depends(get_db)):
    svc = TaskService(db)
    a = svc.assign_task(data)
    return BaseResponse(data={"id": str(a.id)})


@router.post("/proofs", response_model=BaseResponse)
def submit_proof(data: TaskProofCreate, db: Session = Depends(get_db)):
    svc = TaskService(db)
    p = svc.submit_proof(data)
    return BaseResponse(data={"id": str(p.id), "hash": p.proof_hash})
