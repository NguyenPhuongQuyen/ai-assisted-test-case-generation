from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.common.config import get_settings
from app.common.error_handlers import register_exception_handlers
from app.common.logging_config import configure_logging
from app.requirements.router import router as requirements_router
from app.testcases.router import router as testcases_router
from app.users.router import router as users_router

configure_logging()
settings = get_settings()
app = FastAPI(title="AI-assisted Test Case Generator", version="0.1.0")
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
app.include_router(requirements_router, prefix="/api/v1")
app.include_router(testcases_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
