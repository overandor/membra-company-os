import asyncio
from datetime import datetime
from celery import shared_task
from app.agents.all_agents import AGENT_REGISTRY
from app.core.logging import get_logger

logger = get_logger("celery")


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def run_agent_task(self, agent_id: str, query: str, context: dict | None = None):
    """Celery task to run an agent asynchronously."""
    from app.models.schemas import AgentRequest

    if agent_id not in AGENT_REGISTRY:
        raise ValueError(f"Agent {agent_id} not found")

    agent = AGENT_REGISTRY[agent_id]
    request = AgentRequest(query=query, context=context or {})

    try:
        result = asyncio.run(agent.run(request))
        logger.info(
            "agent_task_complete",
            agent_id=agent_id,
            status=result.status,
            query=query[:100],
        )
        return {
            "agent_id": agent_id,
            "status": result.status,
            "output": result.output,
            "tokens_used": result.tokens_used,
            "cost": result.cost,
            "duration_ms": result.duration_ms,
        }
    except Exception as exc:
        logger.error("agent_task_failed", agent_id=agent_id, error=str(exc))
        raise self.retry(exc=exc)


@shared_task
def run_scheduled_agents():
    """Periodic task to check and run due scheduled agents."""
    import os
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/agentworkforce")

    try:
        asyncio.run(_process_schedules())
    except Exception as exc:
        logger.error("scheduled_agents_error", error=str(exc))


async def _process_schedules():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select
    from app.db.models import Schedule
    from app.models.schemas import AgentRequest

    engine = create_async_engine(os.environ["DATABASE_URL"])
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        stmt = select(Schedule).where(Schedule.is_active == True)
        result = await db.execute(stmt)
        schedules = result.scalars().all()

        for sched in schedules:
            now = datetime.utcnow()
            if sched.last_run_at is None or (now - sched.last_run_at).total_seconds() >= 3600:
                if sched.agent_id not in AGENT_REGISTRY:
                    continue
                agent = AGENT_REGISTRY[sched.agent_id]
                request = AgentRequest(query=sched.query, context=sched.context or {})
                try:
                    result = await agent.run(request)
                    sched.last_run_at = now
                    sched.run_count += 1
                    logger.info("scheduled_run_complete", schedule_id=sched.id, agent_id=sched.agent_id)
                except Exception as exc:
                    logger.error("scheduled_run_failed", schedule_id=sched.id, error=str(exc))

        await db.commit()
    await engine.dispose()
