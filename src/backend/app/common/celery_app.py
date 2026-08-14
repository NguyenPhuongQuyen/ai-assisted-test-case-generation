from functools import lru_cache

from celery import Celery

from app.common.config import get_settings
from app.common.constants import AI_GENERATION_QUEUE


@lru_cache
def get_celery_app() -> Celery:
    settings = get_settings()

    app = Celery(
        "testcase_ai",
        broker=settings.celery_broker_url,
        include=["app.testcases.tasks"],
    )
    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        enable_utc=True,
        timezone="UTC",
        task_default_queue=AI_GENERATION_QUEUE,
    )
    return app
