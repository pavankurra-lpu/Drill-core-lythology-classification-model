import os
from celery import Celery
from app.core.config import settings

# Force broker/backend urls from config settings
broker_url = settings.CELERY_BROKER_URL
result_backend = settings.CELERY_RESULT_BACKEND

celery_app = Celery(
    "lithology_tasks",
    broker=broker_url,
    backend=result_backend,
    include=[
        "app.tasks.prediction_tasks",
        "app.tasks.report_tasks",
        "app.tasks.training_tasks"
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600, # 1 hour max
)
