"""IntentOS API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.base import get_db
from app.services.intent import IntentService
from app.schemas.intent import IntentCreate, IntentRead, IntentUpdate, ObjectiveCreate, ObjectiveRead
from app.schemas.common import BaseResponse, PaginatedResponse

router = APIRouter()


@router.post("/", response_model=BaseResponse)
def create_intent(data: IntentCreate, db: Session = Depends(get_db)):
    svc = IntentService(db)
    intent = svc.create_intent(data)
    return BaseResponse(data={"id": str(intent.id), "status": intent.status.value})


@router.get("/", response_model=PaginatedResponse)
def list_intents(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    svc = IntentService(db)
    items = svc.list_intents(user_id=user_id, status=status, limit=limit)
    return PaginatedResponse(
        items=[IntentRead.model_validate(i) for i in items],
        total=len(items),
        page=1,
        page_size=limit,
        pages=1,
    )


@router.get("/{intent_id}", response_model=BaseResponse)
def get_intent(intent_id: str, db: Session = Depends(get_db)):
    svc = IntentService(db)
    intent = svc.db.query(svc.db.bind).first()  # placeholder
    raise HTTPException(status_code=501, detail="Direct get not implemented — use list")


@router.post("/{intent_id}/parse", response_model=BaseResponse)
def parse_intent(intent_id: str, parsed: dict, db: Session = Depends(get_db)):
    svc = IntentService(db)
    intent = svc.parse_intent(intent_id, parsed)
    return BaseResponse(data={"id": str(intent.id), "status": intent.status.value})


@router.post("/{intent_id}/objectives", response_model=BaseResponse)
def create_objectives(intent_id: str, objectives: List[dict], db: Session = Depends(get_db)):
    svc = IntentService(db)
    objs = svc.structure_objectives(intent_id, objectives)
    return BaseResponse(data={"objectives": [{"id": str(o.id), "title": o.title} for o in objs]})
