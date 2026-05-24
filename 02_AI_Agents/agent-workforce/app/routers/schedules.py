from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.base import get_db
from app.db.models import Schedule
from app.models.schemas import ScheduleCreate, ScheduleResponse
from app.agents.all_agents import AGENT_REGISTRY

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.post("/", response_model=ScheduleResponse)
async def create_schedule(schedule_in: ScheduleCreate, db: AsyncSession = Depends(get_db)):
    """Create a new recurring agent schedule."""
    if schedule_in.agent_id not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail="Agent not found")

    schedule = Schedule(
        agent_id=schedule_in.agent_id,
        name=schedule_in.name,
        query=schedule_in.query,
        context=schedule_in.context,
        cron=schedule_in.cron,
        notify_email=schedule_in.notify_email,
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


@router.get("/", response_model=List[ScheduleResponse])
async def list_schedules(limit: int = 100, db: AsyncSession = Depends(get_db)):
    """List all agent schedules."""
    result = await db.execute(select(Schedule).order_by(Schedule.created_at.desc()).limit(limit))
    return result.scalars().all()


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific schedule."""
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


@router.patch("/{schedule_id}/toggle")
async def toggle_schedule(schedule_id: str, db: AsyncSession = Depends(get_db)):
    """Toggle a schedule active/inactive."""
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    schedule.is_active = not schedule.is_active
    await db.commit()
    return {"id": schedule_id, "is_active": schedule.is_active}


@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a schedule."""
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    await db.delete(schedule)
    await db.commit()
    return {"id": schedule_id, "status": "deleted"}
