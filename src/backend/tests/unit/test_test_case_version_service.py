# Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.auth.schemas import CurrentUser
from app.common.constants import AuditAction, ErrorCode, Priority, UserRole
from app.common.constants import TestCaseStatus as CaseStatus
from app.common.exceptions import AppError
from app.testcases.version_service import TestCaseVersionService as VersionService


def make_case(*, created_by=7, lock_version=3, status=CaseStatus.APPROVED):
    return SimpleNamespace(
        id=10,
        requirement_id=2,
        module_id=3,
        summary="Current summary",
        preconditions=["Signed in"],
        steps=["Submit form"],
        expected_result="Saved",
        priority=Priority.HIGH,
        test_techniques=["bva"],
        tags=["regression"],
        review_note="Current note",
        status=status,
        lock_version=lock_version,
        created_by=created_by,
    )


def make_version(number: int, *, summary: str) -> SimpleNamespace:
    return SimpleNamespace(
        test_case_id=10,
        version_number=number,
        snapshot={
            "summary": summary,
            "preconditions": ["Signed in"],
            "steps": ["Submit form"],
            "expected_result": "Saved",
            "priority": "medium",
            "test_techniques": ["ep"],
            "tags": ["smoke"],
            "review_note": None,
            "status": "in_review",
            "lock_version": number,
            "requirement_id": 2,
            "module_id": 3,
        },
        created_by=7,
        created_at=None,
    )


def build_service(case, versions_by_number=None):
    session = SimpleNamespace(commit=AsyncMock())
    test_cases = SimpleNamespace(
        get_by_id=AsyncMock(return_value=case),
        get_by_id_for_update=AsyncMock(return_value=case),
        clear_embedding=AsyncMock(),
        save=AsyncMock(side_effect=lambda item: item),
    )
    versions_by_number = versions_by_number or {}
    versions = SimpleNamespace(
        list_for_test_case=AsyncMock(return_value=list(versions_by_number.values())),
        count_for_test_case=AsyncMock(return_value=len(versions_by_number)),
        get_by_number=AsyncMock(side_effect=lambda _id, number: versions_by_number.get(number)),
        create_snapshot=AsyncMock(),
    )
    audits = SimpleNamespace(create=AsyncMock())
    return VersionService(session, test_cases, versions, audits), session, test_cases, versions, audits


@pytest.mark.asyncio
async def test_owner_can_list_versions() -> None:
    versions = {1: make_version(1, summary="Old"), 2: make_version(2, summary="New")}
    service, _, _, repository, _ = build_service(make_case(), versions)

    items, total = await service.list_versions(10, CurrentUser(id=7, role=UserRole.QA), offset=0, limit=20)

    assert len(items) == 2
    assert total == 2
    repository.list_for_test_case.assert_awaited_once_with(10, offset=0, limit=20)


@pytest.mark.asyncio
async def test_qa_cannot_list_another_users_versions() -> None:
    service, _, _, versions, _ = build_service(make_case(created_by=99))

    with pytest.raises(AppError) as exc_info:
        await service.list_versions(10, CurrentUser(id=7, role=UserRole.QA), offset=0, limit=20)

    assert exc_info.value.code == ErrorCode.FORBIDDEN_RECORD
    versions.list_for_test_case.assert_not_awaited()


@pytest.mark.asyncio
async def test_compare_returns_only_changed_fields() -> None:
    versions = {1: make_version(1, summary="Old"), 2: make_version(2, summary="New")}
    service, _, _, _, _ = build_service(make_case(), versions)

    _, _, changes = await service.compare_versions(10, 1, 2, CurrentUser(id=7, role=UserRole.QA))

    assert changes["summary"] == {"from": "Old", "to": "New"}
    assert "expected_result" not in changes


@pytest.mark.asyncio
async def test_missing_version_returns_404() -> None:
    service, _, _, _, _ = build_service(make_case(), {})

    with pytest.raises(AppError) as exc_info:
        await service.compare_versions(10, 1, 2, CurrentUser(id=7, role=UserRole.QA))

    assert exc_info.value.code == ErrorCode.TEST_CASE_VERSION_NOT_FOUND
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_restore_creates_needs_fix_version_and_audit() -> None:
    case = make_case()
    service, session, test_cases, versions, audits = build_service(case, {1: make_version(1, summary="Old")})

    result = await service.restore_version(10, 1, 3, CurrentUser(id=7, role=UserRole.QA))

    assert result.summary == "Old"
    assert result.priority == Priority.MEDIUM
    assert result.status == CaseStatus.NEEDS_FIX
    assert result.lock_version == 4
    test_cases.clear_embedding.assert_awaited_once_with(10)
    versions.create_snapshot.assert_awaited_once()
    assert audits.create.await_args.args[0].action == AuditAction.RESTORE_TEST_CASE
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_restore_rejects_stale_lock_version() -> None:
    service, _, test_cases, versions, _ = build_service(make_case(lock_version=5), {1: make_version(1, summary="Old")})

    with pytest.raises(AppError) as exc_info:
        await service.restore_version(10, 1, 4, CurrentUser(id=7, role=UserRole.QA))

    assert exc_info.value.code == ErrorCode.CONFLICT
    test_cases.save.assert_not_awaited()
    versions.create_snapshot.assert_not_awaited()


@pytest.mark.asyncio
async def test_admin_cannot_restore_test_case() -> None:
    service, _, _, versions, _ = build_service(make_case(), {1: make_version(1, summary="Old")})

    with pytest.raises(AppError) as exc_info:
        await service.restore_version(10, 1, 3, CurrentUser(id=1, role=UserRole.ADMIN))

    assert exc_info.value.code == ErrorCode.FORBIDDEN_ROLE
    versions.create_snapshot.assert_not_awaited()
