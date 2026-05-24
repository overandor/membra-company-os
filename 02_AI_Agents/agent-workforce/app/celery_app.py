from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "agent_workforce",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.agent_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "run_scheduled_agents_every_minute": {
            "task": "app.tasks.agent_tasks.run_scheduled_agents",
            "schedule": 60.0,
        },
    },
)
