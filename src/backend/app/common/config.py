from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.common.constants import EMBEDDING_DIMENSIONS


class Settings(BaseSettings):
    """Application configuration loaded from environment variables (SE-01, CF-02, CF-05)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(min_length=1)
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = Field(default=60, ge=5, le=60)

    openai_api_key: str = Field(min_length=1)
    openai_model: str = "gpt-5"
    openai_max_output_tokens: int = Field(default=4000, ge=256, le=16000)
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = Field(default=EMBEDDING_DIMENSIONS, ge=1)
    duplicate_similarity_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    ai_rate_limit_max_requests: int = Field(default=10, ge=1, le=100)
    ai_rate_limit_window_seconds: int = Field(default=300, ge=60, le=3600)

    celery_broker_url: str = Field(min_length=1)

    frontend_origin: str = Field(min_length=1)
    log_level: str = "INFO"
    demo_user_password: str = Field(min_length=10)

    @model_validator(mode="after")
    def validate_embedding_dimensions(self) -> "Settings":
        # DB-12: the configured embedding dimension must match the fixed pgvector column dimension.
        if self.openai_embedding_dimensions != EMBEDDING_DIMENSIONS:
            raise ValueError(f"OPENAI_EMBEDDING_DIMENSIONS must be {EMBEDDING_DIMENSIONS}")
        return self


@lru_cache
def get_settings() -> Settings:
    """Load required configuration once; missing mandatory values stop application startup."""
    return Settings()  # type: ignore[call-arg]
