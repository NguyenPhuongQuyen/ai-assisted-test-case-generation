import logging

from app.common.config import get_settings


def configure_logging() -> None:
    """Configure Python logging once; backend code must not use print() as logging (ER-06)."""
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
