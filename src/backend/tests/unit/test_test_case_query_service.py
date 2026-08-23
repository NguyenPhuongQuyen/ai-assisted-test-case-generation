# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.auth.schemas import CurrentUser
from app.common.constants import ErrorCode, UserRole
from app.common.constants import TestCaseStatus as CaseStatus
from app.common.exceptions import AppError
from app.testcases.query_service import TestCaseQueryService as QueryService


def build_service(*, record=None, items=None, total=0):
    repository = SimpleNamespace(
        get_by_id=AsyncMock(return_value=record),
        list_accessible=AsyncMock(return_value=items or []),
        count_accessible=AsyncMock(return_value=total),
    )
    return QueryService(repository), repository


@pytest.mark.asyncio
async def test_qa_list_is_scoped_to_own_test_cases() -> None:
    service, repository = build_service(items=[SimpleNamespace(id=1)], total=1)
    user = CurrentUser(id=7, role=UserRole.QA)

    items, total = await service.list_test_cases(
        user,
        requirement_id=10,
        case_status=CaseStatus.DRAFT,
        offset=0,
        limit=20,
    )

    assert len(items) == 1
    assert total == 1
    repository.list_accessible.assert_awaited_once_with(
        owner_id=7,
        requirement_id=10,
        case_status=CaseStatus.DRAFT,
        offset=0,
        limit=20,
    )
    repository.count_accessible.assert_awaited_once_with(
        owner_id=7,
        requirement_id=10,
        case_status=CaseStatus.DRAFT,
    )


@pytest.mark.asyncio
async def test_manager_list_is_not_limited_to_record_owner() -> None:
    service, repository = build_service(total=2)
    user = CurrentUser(id=2, role=UserRole.MANAGER)

    await service.list_test_cases(user, requirement_id=None, case_status=None, offset=0, limit=20)

    repository.list_accessible.assert_awaited_once_with(
        owner_id=None,
        requirement_id=None,
        case_status=None,
        offset=0,
        limit=20,
    )


@pytest.mark.asyncio
async def test_qa_can_read_own_test_case() -> None:
    record = SimpleNamespace(id=8, created_by=7)
    service, _ = build_service(record=record)

    result = await service.get_test_case(8, CurrentUser(id=7, role=UserRole.QA))

    assert result is record


@pytest.mark.asyncio
async def test_qa_cannot_read_another_users_test_case() -> None:
    record = SimpleNamespace(id=8, created_by=99)
    service, _ = build_service(record=record)

    with pytest.raises(AppError) as exc_info:
        await service.get_test_case(8, CurrentUser(id=7, role=UserRole.QA))

    assert exc_info.value.code == ErrorCode.FORBIDDEN_RECORD
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_missing_test_case_returns_not_found() -> None:
    service, _ = build_service(record=None)

    with pytest.raises(AppError) as exc_info:
        await service.get_test_case(999, CurrentUser(id=7, role=UserRole.QA))

    assert exc_info.value.code == ErrorCode.TEST_CASE_NOT_FOUND
    assert exc_info.value.status_code == 404
