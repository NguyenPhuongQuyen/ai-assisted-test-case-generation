from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    ai_rate_limit_max_requests: int = Field(default=10, ge=1, le=100)
    ai_rate_limit_window_seconds: int = Field(default=300, ge=60, le=3600)

    frontend_origin: str = "http://localhost:3000"
    log_level: str = "INFO"
    demo_user_password: str = Field(default="Demo_Change_Me_123!", min_length=10)


@lru_cache
def get_settings() -> Settings:
    """Load required configuration once; missing mandatory values stop application startup."""
    return Settings()  # type: ignore[call-arg]
