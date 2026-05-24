"""Orchestration API route — converts human intent into objectives, tasks, jobs, gates, proofs."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from app.db.base import get_db
from app.services.orchestration import OrchestrationService
from app.schemas.common import BaseResponse

router = APIRouter()


class OrchestrateRequest(BaseModel):
    intent_text: str
    user_wallet: Optional[str] = None
    user_id: Optional[str] = None
    company_id: Optional[str] = None


@router.post("/", response_model=BaseResponse)
def orchestrate(data: OrchestrateRequest, db: Session = Depends(get_db)):
    svc = OrchestrationService(db)
    result = svc.orchestrate(
        raw_intent=data.intent_text,
        user_wallet=data.user_wallet,
        user_id=data.user_id,
        company_id=data.company_id,
    )
    return BaseResponse(data=result)
