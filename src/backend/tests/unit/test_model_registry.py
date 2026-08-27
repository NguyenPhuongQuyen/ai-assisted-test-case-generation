import importlib
import sys
from unittest.mock import Mock

from app.common.database import Base
from app.common.model_registry import register_orm_models


def test_model_registry_registers_required_tables():
    register_orm_models()

    required_tables = {
        "users",
        "modules",
        "requirements",
        "prompt_configs",
        "generation_jobs",
        "test_cases",
        "test_case_versions",
        "audit_logs",
    }

    assert required_tables <= set(Base.metadata.tables)


def test_worker_registers_models_before_starting_celery(monkeypatch):
    import app.common.model_registry as model_registry

    register = Mock()
    monkeypatch.setattr(
        model_registry,
        "register_orm_models",
        register,
    )

    sys.modules.pop("app.worker", None)
    importlib.import_module("app.worker")

    register.assert_called_once_with()
