"""
Celery application instance.

Task modules (e.g. `batch_prediction_task.py`) are registered here via
`include=` once batch prediction is implemented in Phase 8. This file
is fully functional now so `docker-compose up` can start the worker
process at scaffold stage without errors, even with zero tasks defined.
"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "fraudshield",
    broker=settings.CELERY_BROKER_URL or str(settings.REDIS_URL),
    backend=settings.CELERY_RESULT_BACKEND or str(settings.REDIS_URL),
    include=[
        "app.tasks.batch_prediction_task",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_max_tasks_per_child=100,
)
