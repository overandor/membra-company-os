"""LLM Concierge API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.db.base import get_db
from app.services.llm_concierge import LLMConciergeService
from app.schemas.common import BaseResponse

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    user_wallet: Optional[str] = None
    user_id: Optional[str] = None
    company_id: Optional[str] = None
    chat_history: Optional[List[dict]] = []


class ChatResponse(BaseModel):
    reply: str
    actions_taken: List[str]
    provider: str
    disclaimer: str
    orchestration_result: Optional[dict] = None


@router.post("/chat", response_model=BaseResponse)
async def chat(data: ChatRequest, db: Session = Depends(get_db)):
    svc = LLMConciergeService(db)
    result = await svc.chat(
        message=data.message,
        user_wallet=data.user_wallet,
        user_id=data.user_id,
        company_id=data.company_id,
        chat_history=data.chat_history,
    )
    return BaseResponse(data=result)
