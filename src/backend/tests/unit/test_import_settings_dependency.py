import importlib

from app.common import config, database, security


def test_common_modules_do_not_load_settings_during_import(monkeypatch):
    original_get_settings = config.get_settings

    def fail_if_called():
        raise AssertionError("get_settings must not run during module import")

    monkeypatch.setattr(config, "get_settings", fail_if_called)

    try:
        importlib.reload(security)
        importlib.reload(database)
    finally:
        monkeypatch.setattr(config, "get_settings", original_get_settings)
        importlib.reload(security)
        importlib.reload(database)
