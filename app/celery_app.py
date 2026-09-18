# app/celery_app.py

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "event_conference_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True
)

# 2 scheduled jobs, matching the task's own "event reminder" and
# "session reminder" notifications - the one genuine recurring,
# clock-triggered need in this whole project, unlike food delivery
celery_app.conf.beat_schedule = {
    "daily-event-and-session-reminders": {
        "task": "app.tasks.run_daily_reminder_checks",
        "schedule": crontab(hour=7, minute=0)
    }
}