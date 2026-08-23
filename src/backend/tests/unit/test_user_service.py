# Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.auth.schemas import CurrentUser
from app.common.constants import AuditAction, ErrorCode, UserRole
from app.common.exceptions import AppError
from app.users.schemas import UserCreateRequest, UserUpdateRequest
from app.users.service import UserService


def build_service(users: SimpleNamespace) -> tuple[UserService, AsyncMock, SimpleNamespace]:
    session = AsyncMock()
    audits = SimpleNamespace(create=AsyncMock())
    return UserService(session, users, audits), session, audits


@pytest.mark.asyncio
async def test_non_admin_cannot_create_user() -> None:
    # Arrange
    users = SimpleNamespace(get_by_email=AsyncMock(), create=AsyncMock())
    service, _, _ = build_service(users)
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
    users = SimpleNamespace(get_by_email=AsyncMock(return_value=SimpleNamespace(id=1)), create=AsyncMock())
    service, _, _ = build_service(users)
    payload = UserCreateRequest(email="qa@example.com", password="SafePassword123!", role=UserRole.QA)
    current_user = CurrentUser(id=1, role=UserRole.ADMIN)

    # Act
    with pytest.raises(AppError) as exc_info:
        await service.create_user(payload, current_user)

    # Assert
    assert exc_info.value.code == ErrorCode.USER_ALREADY_EXISTS
    assert exc_info.value.status_code == 409
    users.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_admin_can_list_users_with_pagination() -> None:
    # Arrange
    rows = [SimpleNamespace(id=2, email="qa@example.com", role=UserRole.QA, is_active=True)]
    users = SimpleNamespace(list_page=AsyncMock(return_value=(rows, 1)))
    service, _, _ = build_service(users)

    # Act
    response = await service.list_users(1, 20, CurrentUser(id=1, role=UserRole.ADMIN))

    # Assert
    assert response.total == 1
    assert response.data[0].email == "qa@example.com"
    users.list_page.assert_awaited_once_with(1, 20)


@pytest.mark.asyncio
async def test_admin_update_user_writes_audit_without_password_hash() -> None:
    # Arrange
    user = SimpleNamespace(id=2, email="qa@example.com", role=UserRole.QA, is_active=True, password_hash="old")
    users = SimpleNamespace(get_by_id=AsyncMock(return_value=user), get_by_email=AsyncMock(return_value=None))
    service, session, audits = build_service(users)
    payload = UserUpdateRequest(role=UserRole.MANAGER, is_active=False)

    # Act
    response = await service.update_user(2, payload, CurrentUser(id=1, role=UserRole.ADMIN))

    # Assert
    assert response.role == UserRole.MANAGER
    assert response.is_active is False
    audit = audits.create.await_args.args[0]
    assert audit.action == AuditAction.UPDATE_USER
    assert "password_hash" not in audit.before_state
    assert "password_hash" not in audit.after_state
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_non_admin_cannot_update_user() -> None:
    # Arrange
    users = SimpleNamespace(get_by_id=AsyncMock())
    service, _, _ = build_service(users)

    # Act
    with pytest.raises(AppError) as exc_info:
        await service.update_user(2, UserUpdateRequest(role=UserRole.MANAGER), CurrentUser(id=3, role=UserRole.QA))

    # Assert
    assert exc_info.value.code == ErrorCode.FORBIDDEN_ROLE
    users.get_by_id.assert_not_awaited()
