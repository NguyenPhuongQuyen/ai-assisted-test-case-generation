import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from kombu import Connection
from sqlalchemy import text

from app.auth.router import router as auth_router
from app.common.config import get_settings
from app.common.database import get_session_factory
from app.common.error_handlers import register_exception_handlers
from app.common.logging_config import configure_logging
from app.common.model_registry import register_orm_models
from app.modules.router import router as modules_router
from app.prompt_configs.router import router as prompt_configs_router
from app.requirements.router import router as requirements_router
from app.testcases.router import router as testcases_router
from app.users.router import router as users_router

configure_logging()
register_orm_models()
settings = get_settings()

app = FastAPI(
    title="AI-assisted Test Case Generator",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

register_exception_handlers(app)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(modules_router, prefix="/api/v1")
app.include_router(prompt_configs_router, prefix="/api/v1")
app.include_router(requirements_router, prefix="/api/v1")
app.include_router(testcases_router, prefix="/api/v1")


async def _database_is_healthy() -> bool:
    session_factory = get_session_factory()

    try:
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def _broker_is_healthy() -> bool:
    connection = Connection(
        settings.celery_broker_url,
        connect_timeout=2,
    )

    try:
        connection.ensure_connection(max_retries=0)
        return True
    except Exception:
        return False
    finally:
        connection.release()


@app.get("/health")
async def health() -> JSONResponse:
    database_ok, broker_ok = await asyncio.gather(
        _database_is_healthy(),
        asyncio.to_thread(_broker_is_healthy),
    )

    healthy = database_ok and broker_ok

    return JSONResponse(
        status_code=200 if healthy else 503,
        content={
            "status": "ok" if healthy else "degraded",
            "components": {
                "application": "ok",
                "database": "ok" if database_ok else "down",
                "queue": "ok" if broker_ok else "down",
            },
        },
    )
