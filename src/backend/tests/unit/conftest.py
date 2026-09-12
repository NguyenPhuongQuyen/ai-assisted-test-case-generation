import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://unit_test:unit_test@127.0.0.1:5432/unit_test",
)
os.environ.setdefault(
    "JWT_SECRET",
    "unit-test-jwt-secret-not-for-production-123456",
)
os.environ.setdefault("OPENAI_API_KEY", "unit-test-openai-key")
os.environ.setdefault(
    "CELERY_BROKER_URL",
    "amqp://guest:guest@127.0.0.1:5672//",
)
os.environ.setdefault(
    "FRONTEND_ORIGIN",
    "http://127.0.0.1:3000",
)
os.environ.setdefault(
    "DEMO_USER_PASSWORD",
    "Unit_Test_Demo_123!",
)
