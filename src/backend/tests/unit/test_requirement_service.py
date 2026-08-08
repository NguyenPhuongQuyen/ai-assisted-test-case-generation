from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.auth.schemas import CurrentUser
from app.common.constants import ErrorCode, UserRole
from app.common.exceptions import AppError
from app.requirements.schemas import RequirementCreate
from app.requirements.service import RequirementService


@pytest.mark.asyncio
async def test_non_qa_role_cannot_create_requirement() -> None:
    # Arrange
    session = AsyncMock()
    requirements = SimpleNamespace(create=AsyncMock())
    modules = SimpleNamespace(get_by_id=AsyncMock())
    service = RequirementService(session, requirements, modules)
    payload = RequirementCreate(module_id=1, content="Requirement text that is long enough for validation.")
    user = CurrentUser(id=1, role=UserRole.MANAGER)

    # Act
    with pytest.raises(AppError) as exc_info:
        await service.create_requirement(payload, user)

    # Assert
    assert exc_info.value.code == ErrorCode.FORBIDDEN_ROLE
    modules.get_by_id.assert_not_awaited()
    requirements.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_module_rejects_requirement_creation() -> None:
    # Arrange
    session = AsyncMock()
    requirements = SimpleNamespace(create=AsyncMock())
    modules = SimpleNamespace(get_by_id=AsyncMock(return_value=None))
    service = RequirementService(session, requirements, modules)
    payload = RequirementCreate(module_id=999, content="Requirement text that is long enough for validation.")
    user = CurrentUser(id=1, role=UserRole.QA)

    # Act
    with pytest.raises(AppError) as exc_info:
        await service.create_requirement(payload, user)

    # Assert
    assert exc_info.value.code == ErrorCode.MODULE_NOT_FOUND
    requirements.create.assert_not_awaited()
    session.commit.assert_not_awaited()
