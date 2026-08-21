# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.auth.schemas import CurrentUser
from app.common.constants import AuditAction, ErrorCode, UserRole
from app.common.constants import TestCaseStatus as CaseStatus
from app.common.exceptions import AppError
from app.modules.coverage_repository import ModuleCoverageRecord
from app.modules.schemas import ModuleCreateRequest, ModuleUpdateRequest
from app.modules.schemas import TestCaseTagUpdateRequest as TagUpdateRequest
from app.modules.service import ModuleService


def build_service(*, module=None, duplicate: bool = False, coverage=None, test_case=None):
    session = SimpleNamespace(commit=AsyncMock())
    modules = SimpleNamespace(
        get_by_id=AsyncMock(return_value=module),
        exists_with_name=AsyncMock(return_value=duplicate),
        create=AsyncMock(side_effect=lambda value: value),
        save=AsyncMock(side_effect=lambda value: value),
        list_all=AsyncMock(return_value=[]),
        count_all=AsyncMock(return_value=0),
    )
    coverage_repo = SimpleNamespace(get_coverage=AsyncMock(return_value=coverage))
    test_cases = SimpleNamespace(
        get_by_id=AsyncMock(return_value=test_case),
        save=AsyncMock(side_effect=lambda value: value),
    )
    audits = SimpleNamespace(create=AsyncMock())
    service = ModuleService(session, modules, coverage_repo, test_cases, audits)
    return service, session, modules, coverage_repo, test_cases, audits


@pytest.mark.asyncio
async def test_non_manager_cannot_create_module() -> None:
    service, session, modules, _, _, _ = build_service()

    with pytest.raises(AppError) as exc_info:
        await service.create_module(ModuleCreateRequest(name="Checkout"), CurrentUser(id=7, role=UserRole.QA))

    assert exc_info.value.code == ErrorCode.FORBIDDEN_ROLE
    modules.create.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_manager_creates_root_module_and_audits() -> None:
    service, session, modules, _, _, audits = build_service()
    modules.get_by_id.return_value = None

    module = await service.create_module(
        ModuleCreateRequest(name="Checkout"),
        CurrentUser(id=2, role=UserRole.MANAGER),
    )

    assert module.name == "Checkout"
    assert module.created_by == 2
    audit = audits.create.await_args.args[0]
    assert audit.action == AuditAction.CREATE_MODULE
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_duplicate_sibling_name_returns_conflict() -> None:
    service, session, modules, _, _, _ = build_service(duplicate=True)

    with pytest.raises(AppError) as exc_info:
        await service.create_module(
            ModuleCreateRequest(name="Checkout"),
            CurrentUser(id=2, role=UserRole.MANAGER),
        )

    assert exc_info.value.code == ErrorCode.CONFLICT
    modules.create.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_rejects_direct_parent_cycle() -> None:
    module = SimpleNamespace(id=3, name="Checkout", parent_id=None)
    service, session, modules, _, _, _ = build_service(module=module)

    with pytest.raises(AppError) as exc_info:
        await service.update_module(
            3,
            ModuleUpdateRequest(parent_id=3),
            CurrentUser(id=2, role=UserRole.MANAGER),
        )

    assert exc_info.value.code == ErrorCode.VALIDATION_ERROR
    modules.save.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_manager_tags_only_test_case_in_selected_module() -> None:
    module = SimpleNamespace(id=3, name="Checkout", parent_id=None)
    test_case = SimpleNamespace(id=10, module_id=3, tags=["old"])
    service, session, _, _, test_cases, audits = build_service(module=module, test_case=test_case)

    updated = await service.update_test_case_tags(
        3,
        10,
        TagUpdateRequest(tags=["Boundary", "boundary", "Payment"]),
        CurrentUser(id=2, role=UserRole.MANAGER),
    )

    assert updated.tags == ["boundary", "payment"]
    test_cases.save.assert_awaited_once_with(test_case)
    audit = audits.create.await_args.args[0]
    assert audit.action == AuditAction.TAG_TEST_CASE
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_tagging_test_case_from_another_module_is_forbidden() -> None:
    module = SimpleNamespace(id=3, name="Checkout", parent_id=None)
    test_case = SimpleNamespace(id=10, module_id=9, tags=[])
    service, session, _, _, test_cases, _ = build_service(module=module, test_case=test_case)

    with pytest.raises(AppError) as exc_info:
        await service.update_test_case_tags(
            3,
            10,
            TagUpdateRequest(tags=["payment"]),
            CurrentUser(id=2, role=UserRole.MANAGER),
        )

    assert exc_info.value.code == ErrorCode.FORBIDDEN_RECORD
    test_cases.save.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_qa_coverage_is_scoped_to_owned_records() -> None:
    module = SimpleNamespace(id=3, name="Checkout", parent_id=None)
    coverage = ModuleCoverageRecord(
        total_requirements=4,
        covered_requirements=3,
        total_test_cases=8,
        approved_test_cases=5,
        status_counts={status: (5 if status == CaseStatus.APPROVED else 0) for status in CaseStatus},
    )
    service, _, _, coverage_repo, _, _ = build_service(module=module, coverage=coverage)

    response = await service.get_coverage(3, CurrentUser(id=7, role=UserRole.QA))

    coverage_repo.get_coverage.assert_awaited_once_with(module_id=3, owner_id=7)
    assert response.requirement_coverage_percent == 75.0
    assert response.approved_test_cases == 5


@pytest.mark.asyncio
async def test_manager_coverage_is_not_owner_scoped() -> None:
    module = SimpleNamespace(id=3, name="Checkout", parent_id=None)
    coverage = ModuleCoverageRecord(
        total_requirements=0,
        covered_requirements=0,
        total_test_cases=0,
        approved_test_cases=0,
        status_counts={status: 0 for status in CaseStatus},
    )
    service, _, _, coverage_repo, _, _ = build_service(module=module, coverage=coverage)

    response = await service.get_coverage(3, CurrentUser(id=2, role=UserRole.MANAGER))

    coverage_repo.get_coverage.assert_awaited_once_with(module_id=3, owner_id=None)
    assert response.requirement_coverage_percent == 0.0
