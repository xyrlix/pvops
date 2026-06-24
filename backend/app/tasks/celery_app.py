"""Celery 应用配置."""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "pvops",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.sample_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=1800,
    worker_prefetch_multiplier=1,
)
