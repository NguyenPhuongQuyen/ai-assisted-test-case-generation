from app.common.celery_app import get_celery_app
from app.common.constants import AI_GENERATION_QUEUE, GENERATION_TASK_NAME


class GenerationTaskQueue:
    def enqueue(self, job_id: int) -> None:
        get_celery_app().send_task(
            GENERATION_TASK_NAME,
            args=[job_id],
            queue=AI_GENERATION_QUEUE,
        )
