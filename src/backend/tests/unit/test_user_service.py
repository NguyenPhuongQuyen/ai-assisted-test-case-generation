from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.auth.schemas import CurrentUser
from app.common.constants import ErrorCode, UserRole
from app.common.exceptions import AppError
from app.users.schemas import UserCreateRequest
from app.users.service import UserService


@pytest.mark.asyncio
async def test_non_admin_cannot_create_user() -> None:
    # Arrange
    session = AsyncMock()
    users = SimpleNamespace(get_by_email=AsyncMock(), create=AsyncMock())
    service = UserService(session, users)
    payload = UserCreateRequest(email="newqa@example.com", password="SafePassword123!", role=UserRole.QA)
    current_user = CurrentUser(id=7, role=UserRole.QA)

    # Act
    with pytest.raises(AppError) as exc_info:
        await service.create_user(payload, current_user)

    # Assert
    assert exc_info.value.code == ErrorCode.FORBIDDEN_ROLE
    users.get_by_email.assert_not_awaited()
    users.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_admin_cannot_create_duplicate_email() -> None:
    # Arrange
    session = AsyncMock()
    users = SimpleNamespace(get_by_email=AsyncMock(return_value=SimpleNamespace(id=1)), create=AsyncMock())
    service = UserService(session, users)
    payload = UserCreateRequest(email="qa@example.com", password="SafePassword123!", role=UserRole.QA)
    current_user = CurrentUser(id=1, role=UserRole.ADMIN)

    # Act
    with pytest.raises(AppError) as exc_info:
        await service.create_user(payload, current_user)

    # Assert
    assert exc_info.value.code == ErrorCode.USER_ALREADY_EXISTS
    assert exc_info.value.status_code == 409
    users.create.assert_not_awaited()
