from celery import Celery

from app.config import settings

celery_app = Celery(
    "dam",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.tasks.ingest.*": {"queue": "ingest"},
        "app.tasks.transcode.*": {"queue": "ingest"},
        "app.tasks.ai_tag.*": {"queue": "ai"},
    },
)
