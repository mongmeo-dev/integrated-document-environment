from celery import Celery

from ide_api.config import get_settings

settings = get_settings()

app = Celery(
    "ide_api",
    broker=settings.redis_url,
    include=["ide_api.domains.impacts.tasks"],
)
app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "recover-queued-relationship-analyses": {
            "task": "ide_api.impacts.recover_queued_relationship_analyses",
            "schedule": 60.0,
        }
    },
)
