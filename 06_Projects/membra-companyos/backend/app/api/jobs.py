"""JobOS API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.base import get_db
from app.services.job import JobService
from app.schemas.job import JobCreate, JobRead, JobUpdate, BountyCreate, WorkOrderCreate, MarketplaceActionCreate, JobProofCreate
from app.schemas.common import BaseResponse, PaginatedResponse

router = APIRouter()


@router.post("/", response_model=BaseResponse)
def create_job(data: JobCreate, db: Session = Depends(get_db)):
    svc = JobService(db)
    job = svc.create_job(data)
    return BaseResponse(data={"id": str(job.id), "status": job.status.value, "type": job.job_type.value})


@router.get("/", response_model=PaginatedResponse)
def list_jobs(
    company_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    svc = JobService(db)
    items = svc.list_jobs(company_id=company_id, status=status, limit=limit)
    return PaginatedResponse(
        items=[JobRead.model_validate(j) for j in items],
        total=len(items),
        page=1,
        page_size=limit,
        pages=1,
    )


@router.get("/{job_id}", response_model=BaseResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    from uuid import UUID as PyUUID
    job = db.query(Job).filter(Job.id == PyUUID(job_id)).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return BaseResponse(data={
        "id": str(job.id),
        "title": job.title,
        "status": job.status.value,
        "type": job.job_type.value,
        "description": job.description,
        "budget": str(job.budget) if job.budget else None,
        "currency": job.currency,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    })


@router.patch("/{job_id}", response_model=BaseResponse)
def update_job(job_id: str, data: JobUpdate, db: Session = Depends(get_db)):
    svc = JobService(db)
    job = svc.update_job(job_id, data)
    return BaseResponse(data={"id": str(job.id), "status": job.status.value})


@router.post("/{job_id}/complete", response_model=BaseResponse)
def complete_job(job_id: str, proof_hash: Optional[str] = None, db: Session = Depends(get_db)):
    svc = JobService(db)
    job = svc.complete_job(job_id, proof_hash)
    return BaseResponse(data={"id": str(job.id), "status": job.status.value, "completed_at": job.completed_at.isoformat() if job.completed_at else None})


@router.post("/bounties", response_model=BaseResponse)
def create_bounty(data: BountyCreate, db: Session = Depends(get_db)):
    svc = JobService(db)
    bounty = svc.create_bounty(data)
    return BaseResponse(data={"id": str(bounty.id), "reward": str(bounty.reward_amount)})


@router.post("/work-orders", response_model=BaseResponse)
def create_work_order(data: WorkOrderCreate, db: Session = Depends(get_db)):
    svc = JobService(db)
    wo = svc.create_work_order(data)
    return BaseResponse(data={"id": str(wo.id), "wo_number": wo.wo_number})


@router.post("/marketplace-actions", response_model=BaseResponse)
def create_marketplace_action(data: MarketplaceActionCreate, db: Session = Depends(get_db)):
    svc = JobService(db)
    action = svc.create_marketplace_action(data)
    return BaseResponse(data={"id": str(action.id), "status": action.status})


@router.post("/proofs", response_model=BaseResponse)
def submit_job_proof(data: JobProofCreate, db: Session = Depends(get_db)):
    svc = JobService(db)
    proof = svc.submit_job_proof(data)
    return BaseResponse(data={"id": str(proof.id), "proof_hash": proof.proof_hash, "status": proof.verification_status})
