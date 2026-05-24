"""MEMBRA CompanyOS — JobOS service."""
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.job import Job, JobStatus, JobType, Bounty, WorkOrder, MarketplaceAction, JobProof
from app.schemas.job import JobCreate, JobUpdate, BountyCreate, WorkOrderCreate, MarketplaceActionCreate, JobProofCreate
from app.core.logging import get_logger
from app.services.proofbook import ProofBookService
from app.services.governance import GovernanceService

logger = get_logger(__name__)


class JobService:
    def __init__(self, db: Session):
        self.db = db
        self.proof = ProofBookService(db)
        self.gov = GovernanceService(db)

    def create_job(self, data: JobCreate) -> Job:
        job = Job(
            task_id=UUID(data.task_id) if data.task_id else None,
            company_id=UUID(data.company_id) if data.company_id else None,
            title=data.title,
            description=data.description,
            job_type=JobType(data.job_type),
            budget=data.budget,
            currency=data.currency,
            assigned_to=UUID(data.assigned_to) if data.assigned_to else None,
            assigned_agent_id=UUID(data.assigned_agent_id) if data.assigned_agent_id else None,
            asset_id=UUID(data.asset_id) if data.asset_id else None,
            location_json=data.location_json or {},
            requirements=data.requirements or [],
            deliverables=data.deliverables or [],
            deadline=data.deadline,
            metadata_json=data.metadata_json or {},
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        self.proof.write_entry(
            entry_type="TASK_CREATED",
            resource_type="job",
            resource_id=job.id,
            actor_type="system",
            actor_id=job.assigned_to or UUID("00000000-0000-0000-0000-000000000000"),
            description=f"Job created: {data.title}",
            data={"job_type": data.job_type, "budget": str(data.budget) if data.budget else None},
        )
        return job

    def update_job(self, job_id: str, data: JobUpdate) -> Job:
        job = self.db.query(Job).filter(Job.id == UUID(job_id)).first()
        if not job:
            raise ValueError("Job not found")
        for field, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(job, field, value)
        self.db.commit()
        self.db.refresh(job)
        return job

    def complete_job(self, job_id: str, proof_hash: Optional[str] = None) -> Job:
        job = self.db.query(Job).filter(Job.id == UUID(job_id)).first()
        if not job:
            raise ValueError("Job not found")
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now(timezone.utc)
        job.proof_hash = proof_hash
        self.db.commit()
        self.db.refresh(job)
        self.proof.write_entry(
            entry_type="JOB_COMPLETED",
            resource_type="job",
            resource_id=job.id,
            actor_type="system",
            actor_id=job.assigned_to or UUID("00000000-0000-0000-0000-000000000000"),
            description=f"Job completed: {job.title}",
            data={"proof_hash": proof_hash},
        )
        return job

    def create_bounty(self, data: BountyCreate) -> Bounty:
        bounty = Bounty(
            job_id=UUID(data.job_id) if data.job_id else None,
            title=data.title,
            description=data.description,
            reward_amount=data.reward_amount,
            currency=data.currency,
            requirements=data.requirements or [],
            deadline=data.deadline,
        )
        self.db.add(bounty)
        self.db.commit()
        self.db.refresh(bounty)
        return bounty

    def create_work_order(self, data: WorkOrderCreate) -> WorkOrder:
        wo = WorkOrder(
            job_id=UUID(data.job_id) if data.job_id else None,
            wo_number=data.wo_number,
            title=data.title,
            crew_assignment=data.crew_assignment or [],
            schedule_json=data.schedule_json or {},
            equipment_json=data.equipment_json or [],
            cost_estimate=data.cost_estimate,
        )
        self.db.add(wo)
        self.db.commit()
        self.db.refresh(wo)
        return wo

    def create_marketplace_action(self, data: MarketplaceActionCreate) -> MarketplaceAction:
        action = MarketplaceAction(
            job_id=UUID(data.job_id) if data.job_id else None,
            action_type=data.action_type,
            asset_type=data.asset_type,
            asset_id=UUID(data.asset_id) if data.asset_id else None,
            listing_price=data.listing_price,
            visibility=data.visibility,
        )
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        return action

    def submit_job_proof(self, data: JobProofCreate) -> JobProof:
        import hashlib
        from datetime import datetime, timezone
        proof_data = data.proof_data or {}
        canonical = str(sorted(proof_data.items())) if isinstance(proof_data, dict) else str(proof_data)
        proof_hash = hashlib.sha3_256(canonical.encode()).hexdigest()
        proof = JobProof(
            job_id=UUID(data.job_id),
            proof_type=data.proof_type,
            proof_data=proof_data,
            ipfs_cid=data.ipfs_cid,
            proof_hash=proof_hash,
        )
        self.db.add(proof)
        self.db.commit()
        self.db.refresh(proof)
        self.proof.write_entry(
            entry_type="JOB_COMPLETED",
            resource_type="job_proof",
            resource_id=proof.id,
            actor_type="human",
            actor_id=UUID(data.submitted_by) if data.submitted_by else UUID("00000000-0000-0000-0000-000000000000"),
            description=f"Proof submitted for job {data.job_id}: {data.proof_type}",
            data={"proof_type": data.proof_type, "hash": proof_hash},
        )
        job = self.db.query(Job).filter(Job.id == UUID(data.job_id)).first()
        if job:
            all_proofs = self.db.query(JobProof).filter(JobProof.job_id == job.id).all()
            requirements = job.deliverables or []
            if requirements and len(all_proofs) >= len(requirements):
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now(timezone.utc)
                self.db.commit()
                self.db.refresh(job)
        return proof

    def list_jobs(self, company_id: Optional[str] = None, status: Optional[str] = None, limit: int = 50) -> List[Job]:
        q = self.db.query(Job)
        if company_id:
            q = q.filter(Job.company_id == UUID(company_id))
        if status:
            q = q.filter(Job.status == JobStatus(status))
        return q.order_by(Job.created_at.desc()).limit(limit).all()
