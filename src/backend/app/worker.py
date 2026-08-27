from app.common.celery_app import get_celery_app
from app.common.model_registry import register_orm_models

register_orm_models()
celery_app = get_celery_app()
