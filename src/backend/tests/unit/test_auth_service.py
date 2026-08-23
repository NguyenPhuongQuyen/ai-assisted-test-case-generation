from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.auth.schemas import LoginRequest
from app.auth.service import AuthService
from app.common.constants import ErrorCode, UserRole
from app.common.exceptions import AppError


@pytest.mark.asyncio
async def test_locked_account_cannot_login() -> None:
    # Arrange
    session = AsyncMock()
    user = SimpleNamespace(
        id=1,
        email="qa@example.com",
        password_hash="$2b$12$placeholder",
        role=UserRole.QA,
        failed_login_attempts=5,
        locked_until=datetime.now(UTC) + timedelta(minutes=10),
        is_active=True,
    )
    users = SimpleNamespace(get_by_email=AsyncMock(return_value=user))
    service = AuthService(session, users)
    payload = LoginRequest(email="qa@example.com", password="WrongPassword123!")

    # Act
    with pytest.raises(AppError) as exc_info:
        await service.login(payload)

    # Assert
    assert exc_info.value.code == ErrorCode.ACCOUNT_LOCKED
    assert exc_info.value.status_code == 429


@pytest.mark.asyncio
async def test_disabled_account_cannot_login() -> None:
    # Arrange
    session = AsyncMock()
    user = SimpleNamespace(
        id=2,
        email="disabled@example.com",
        password_hash="$2b$12$placeholder",
        role=UserRole.QA,
        failed_login_attempts=0,
        locked_until=None,
        is_active=False,
    )
    service = AuthService(session, SimpleNamespace(get_by_email=AsyncMock(return_value=user)))

    # Act
    with pytest.raises(AppError) as exc_info:
        await service.login(LoginRequest(email="disabled@example.com", password="SafePassword123!"))

    # Assert
    assert exc_info.value.code == ErrorCode.ACCOUNT_DISABLED
    assert exc_info.value.status_code == 403
    session.commit.assert_not_awaited()
