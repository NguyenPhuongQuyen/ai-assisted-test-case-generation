import asyncio
from collections.abc import Callable, Generator
from typing import Any

import pytest
from app.common.config import get_settings
from app.common.security import hash_password
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

settings = get_settings()
database_url = settings.database_url

if make_url(database_url).database != "testcase_ai_test":
    raise RuntimeError("Integration test chi duoc chay tren database testcase_ai_test.")

from app.main import app  # noqa: E402

TEST_PASSWORD = "Integration_Test_123!"


async def reset_database(password_hash: str) -> None:
    engine = create_async_engine(database_url)

    async with engine.begin() as connection:
        await connection.execute(
            text(
                """
                TRUNCATE TABLE
                    audit_logs,
                    test_case_versions,
                    test_cases,
                    generation_jobs,
                    requirements,
                    modules,
                    prompt_configs,
                    users
                RESTART IDENTITY CASCADE
                """
            )
        )

        users = [
            ("admin.integration@example.com", "admin"),
            ("manager.integration@example.com", "manager"),
            ("qa.integration@example.com", "qa"),
        ]

        for email, role in users:
            await connection.execute(
                text(
                    """
                    INSERT INTO users (
                        email,
                        password_hash,
                        role,
                        failed_login_attempts,
                        is_active
                    )
                    VALUES (
                        :email,
                        :password_hash,
                        :role,
                        0,
                        true
                    )
                    """
                ),
                {
                    "email": email,
                    "password_hash": password_hash,
                    "role": role,
                },
            )

    await engine.dispose()


async def read_rows(
    statement: str,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    engine = create_async_engine(database_url)

    async with engine.connect() as connection:
        result = await connection.execute(text(statement), params or {})
        rows = [dict(row) for row in result.mappings().all()]

    await engine.dispose()
    return rows


async def write_rows(
    statement: str,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    engine = create_async_engine(database_url)

    async with engine.begin() as connection:
        result = await connection.execute(text(statement), params or {})
        rows = [dict(row) for row in result.mappings().all()]

    await engine.dispose()
    return rows


@pytest.fixture(scope="session")
def password_hash() -> str:
    return hash_password(TEST_PASSWORD)


@pytest.fixture(autouse=True)
def clean_test_database(password_hash: str) -> None:
    asyncio.run(reset_database(password_hash))


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def login(
    client: TestClient,
) -> Callable[[str], dict[str, str]]:
    def do_login(email: str) -> dict[str, str]:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": TEST_PASSWORD,
            },
        )

        assert response.status_code == 200
        token = response.json()["access_token"]

        return {
            "Authorization": f"Bearer {token}",
        }

    return do_login


@pytest.fixture
def database_rows() -> Callable[
    [str, dict[str, Any] | None],
    list[dict[str, Any]],
]:
    def query(
        statement: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return asyncio.run(read_rows(statement, params))

    return query


@pytest.fixture
def database_write() -> Callable[
    [str, dict[str, Any] | None],
    list[dict[str, Any]],
]:
    def execute(
        statement: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return asyncio.run(write_rows(statement, params))

    return execute
