# Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.auth.schemas import CurrentUser
from app.common.constants import AuditAction, ErrorCode, UserRole
from app.common.constants import TestCaseStatus as CaseStatus
from app.common.exceptions import AppError
from app.requirements.schemas import RequirementCreate, RequirementUpdate
from app.requirements.service import RequirementService


def make_requirement(*, created_by=7, lock_version=1):
    return SimpleNamespace(
        id=5,
        module_id=1,
        content="Original requirement text that is long enough for validation.",
        acceptance_criteria="Original acceptance criteria",
        lock_version=lock_version,
        created_by=created_by,
    )


def make_case(case_id: int, status: CaseStatus):
    return SimpleNamespace(
        id=case_id,
        requirement_id=5,
        module_id=1,
        summary=f"Case {case_id}",
        preconditions=[],
        steps=["Run step"],
        expected_result="Expected",
        priority=SimpleNamespace(value="high"),
        test_techniques=[],
        tags=[],
        review_note=None,
        status=status,
        lock_version=2,
        created_by=7,
    )


def build_service(requirement=None, related_cases=None):
    session = SimpleNamespace(commit=AsyncMock())
    requirements = SimpleNamespace(
        create=AsyncMock(side_effect=lambda item: item),
        get_by_id_for_update=AsyncMock(return_value=requirement),
        save=AsyncMock(side_effect=lambda item: item),
    )
    modules = SimpleNamespace(get_by_id=AsyncMock(return_value=SimpleNamespace(id=1)))
    test_cases = SimpleNamespace(
        list_requirement_revalidation_candidates_for_update=AsyncMock(return_value=related_cases or []),
        save=AsyncMock(side_effect=lambda item: item),
    )
    versions = SimpleNamespace(create_snapshot=AsyncMock())
    audits = SimpleNamespace(create=AsyncMock())
    service = RequirementService(session, requirements, modules, test_cases, versions, audits)
    return service, session, requirements, modules, test_cases, versions, audits


@pytest.mark.asyncio
async def test_non_qa_role_cannot_create_requirement() -> None:
    service, _, requirements, modules, _, _, _ = build_service()
    payload = RequirementCreate(module_id=1, content="Requirement text that is long enough for validation.")

    with pytest.raises(AppError) as exc_info:
        await service.create_requirement(payload, CurrentUser(id=1, role=UserRole.MANAGER))

    assert exc_info.value.code == ErrorCode.FORBIDDEN_ROLE
    modules.get_by_id.assert_not_awaited()
    requirements.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_module_rejects_requirement_creation() -> None:
    service, session, requirements, modules, _, _, _ = build_service()
    modules.get_by_id.return_value = None
    payload = RequirementCreate(module_id=999, content="Requirement text that is long enough for validation.")

    with pytest.raises(AppError) as exc_info:
        await service.create_requirement(payload, CurrentUser(id=1, role=UserRole.QA))

    assert exc_info.value.code == ErrorCode.MODULE_NOT_FOUND
    requirements.create.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_requirement_records_audit() -> None:
    service, session, _, _, _, _, audits = build_service()
    payload = RequirementCreate(module_id=1, content="Requirement text that is long enough for validation.")

    result = await service.create_requirement(payload, CurrentUser(id=7, role=UserRole.QA))

    assert result.created_by == 7
    assert audits.create.await_args.args[0].action == AuditAction.CREATE_REQUIREMENT
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_requirement_marks_approved_cases_needs_fix() -> None:
    requirement = make_requirement()
    approved = make_case(10, CaseStatus.APPROVED)
    exported = make_case(11, CaseStatus.EXPORTED)
    service, session, _, _, test_cases, versions, audits = build_service(requirement, [approved, exported])
    payload = RequirementUpdate(lock_version=1, content="Updated requirement text that is long enough for validation.")

    result = await service.update_requirement(5, payload, CurrentUser(id=7, role=UserRole.QA))

    assert result.lock_version == 2
    assert approved.status == CaseStatus.NEEDS_FIX
    assert exported.status == CaseStatus.NEEDS_FIX
    assert approved.lock_version == 3
    assert versions.create_snapshot.await_count == 2
    assert test_cases.save.await_count == 2
    audit = audits.create.await_args.args[0]
    assert audit.action == AuditAction.UPDATE_REQUIREMENT
    assert audit.after_state["affected_test_case_ids"] == [10, 11]
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_qa_cannot_update_another_users_requirement() -> None:
    service, _, requirements, _, test_cases, _, _ = build_service(make_requirement(created_by=99))

    with pytest.raises(AppError) as exc_info:
        await service.update_requirement(
            5,
            RequirementUpdate(lock_version=1, acceptance_criteria="Updated criteria"),
            CurrentUser(id=7, role=UserRole.QA),
        )

    assert exc_info.value.code == ErrorCode.FORBIDDEN_RECORD
    requirements.save.assert_not_awaited()
    test_cases.list_requirement_revalidation_candidates_for_update.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_requirement_rejects_stale_lock_version() -> None:
    service, _, requirements, _, test_cases, _, _ = build_service(make_requirement(lock_version=3))

    with pytest.raises(AppError) as exc_info:
        await service.update_requirement(
            5,
            RequirementUpdate(lock_version=2, acceptance_criteria="Updated criteria"),
            CurrentUser(id=7, role=UserRole.QA),
        )

    assert exc_info.value.code == ErrorCode.CONFLICT
    requirements.save.assert_not_awaited()
    test_cases.list_requirement_revalidation_candidates_for_update.assert_not_awaited()
