from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.auth.schemas import CurrentUser
from app.common.constants import (
    AuditAction,
    ErrorCode,
    Priority,
    UserRole,
)
from app.common.constants import TestCaseStatus as CaseStatus
from app.common.exceptions import AppError
from app.testcases.duplicate_merge_service import (
    DuplicateMergeService,
)


def make_case(
    *,
    test_case_id: int,
    created_by: int = 7,
    requirement_id: int = 2,
    module_id: int = 3,
    status: CaseStatus = CaseStatus.DRAFT,
    lock_version: int = 2,
    priority: Priority = Priority.MEDIUM,
):
    return SimpleNamespace(
        id=test_case_id,
        requirement_id=requirement_id,
        module_id=module_id,
        summary=f"Test case {test_case_id}",
        preconditions=["User is signed in"],
        steps=[f"Step from TC {test_case_id}"],
        expected_result=f"Expected result {test_case_id}",
        priority=priority,
        test_techniques=["EP"],
        tags=[],
        review_note=None,
        status=status,
        lock_version=lock_version,
        created_by=created_by,
    )


def build_service(
    target,
    source,
    *,
    similarity: float | None = 0.91,
):
    session = SimpleNamespace(commit=AsyncMock())
    test_cases = SimpleNamespace(
        get_by_id_for_update=AsyncMock(side_effect=[target, source]),
        get_duplicate_similarity=AsyncMock(return_value=similarity),
        clear_embedding=AsyncMock(),
        save=AsyncMock(side_effect=lambda item: item),
    )
    versions = SimpleNamespace(create_snapshot=AsyncMock())
    audits = SimpleNamespace(create=AsyncMock())

    service = DuplicateMergeService(
        session=session,
        test_cases=test_cases,
        versions=versions,
        audits=audits,
    )
    return (
        service,
        session,
        test_cases,
        versions,
        audits,
    )


@pytest.mark.asyncio
async def test_merge_keeps_target_and_rejects_source() -> None:
    target = make_case(
        test_case_id=10,
        status=CaseStatus.IN_REVIEW,
        priority=Priority.MEDIUM,
    )
    source = make_case(
        test_case_id=11,
        priority=Priority.HIGH,
    )

    service, session, test_cases, versions, audits = build_service(target, source)

    result, source_id, similarity = await service.merge(
        target_id=10,
        source_id=11,
        target_lock_version=2,
        current_user=CurrentUser(
            id=7,
            role=UserRole.QA,
        ),
    )

    assert result is target
    assert source_id == 11
    assert similarity == 0.91

    assert target.priority == Priority.HIGH
    assert target.status == CaseStatus.NEEDS_FIX
    assert target.lock_version == 3
    assert "TC #11" in target.review_note

    assert source.status == CaseStatus.REJECTED
    assert source.lock_version == 3
    assert "TC #10" in source.review_note

    assert test_cases.clear_embedding.await_count == 2
    assert test_cases.save.await_count == 2
    assert versions.create_snapshot.await_count == 2
    assert audits.create.await_count == 2

    target_audit = audits.create.await_args_list[0].args[0]
    source_audit = audits.create.await_args_list[1].args[0]

    assert target_audit.action == AuditAction.EDIT_TEST_CASE
    assert target_audit.after_state["merged_from_test_case_id"] == 11

    assert source_audit.action == AuditAction.REJECT_TEST_CASE
    assert source_audit.after_state["merged_into_test_case_id"] == 10

    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_merge_can_keep_traceability_across_requirements() -> None:
    target = make_case(
        test_case_id=10,
        requirement_id=2,
    )
    source = make_case(
        test_case_id=11,
        requirement_id=9,
    )

    service, _, _, _, _ = build_service(
        target,
        source,
    )

    result, source_id, _ = await service.merge(
        target_id=10,
        source_id=11,
        target_lock_version=2,
        current_user=CurrentUser(
            id=7,
            role=UserRole.QA,
        ),
    )

    assert result.requirement_id == 2
    assert source.requirement_id == 9
    assert source_id == 11
    assert source.status == CaseStatus.REJECTED


@pytest.mark.asyncio
async def test_cannot_merge_case_with_itself() -> None:
    target = make_case(test_case_id=10)
    service, session, _, _, _ = build_service(
        target,
        target,
    )

    with pytest.raises(AppError) as exc_info:
        await service.merge(
            target_id=10,
            source_id=10,
            target_lock_version=2,
            current_user=CurrentUser(
                id=7,
                role=UserRole.QA,
            ),
        )

    assert exc_info.value.code == ErrorCode.VALIDATION_ERROR
    assert exc_info.value.status_code == 422
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_stale_target_lock_is_rejected() -> None:
    target = make_case(
        test_case_id=10,
        lock_version=4,
    )
    source = make_case(test_case_id=11)

    service, session, test_cases, _, _ = build_service(target, source)

    with pytest.raises(AppError) as exc_info:
        await service.merge(
            target_id=10,
            source_id=11,
            target_lock_version=3,
            current_user=CurrentUser(
                id=7,
                role=UserRole.QA,
            ),
        )

    assert exc_info.value.code == ErrorCode.CONFLICT
    assert exc_info.value.status_code == 409
    test_cases.save.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_qa_cannot_merge_another_users_source() -> None:
    target = make_case(test_case_id=10)
    source = make_case(
        test_case_id=11,
        created_by=99,
    )

    service, session, test_cases, _, _ = build_service(target, source)

    with pytest.raises(AppError) as exc_info:
        await service.merge(
            target_id=10,
            source_id=11,
            target_lock_version=2,
            current_user=CurrentUser(
                id=7,
                role=UserRole.QA,
            ),
        )

    assert exc_info.value.code == ErrorCode.FORBIDDEN_RECORD
    assert exc_info.value.status_code == 403
    test_cases.save.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_merge_requires_same_module() -> None:
    target = make_case(
        test_case_id=10,
        module_id=3,
    )
    source = make_case(
        test_case_id=11,
        module_id=8,
    )

    service, session, test_cases, _, _ = build_service(target, source)

    with pytest.raises(AppError) as exc_info:
        await service.merge(
            target_id=10,
            source_id=11,
            target_lock_version=2,
            current_user=CurrentUser(
                id=7,
                role=UserRole.QA,
            ),
        )

    assert exc_info.value.code == ErrorCode.CONFLICT
    assert exc_info.value.status_code == 409
    test_cases.get_duplicate_similarity.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_merge_rejects_pair_below_threshold() -> None:
    target = make_case(test_case_id=10)
    source = make_case(test_case_id=11)

    service, session, test_cases, versions, audits = build_service(
        target,
        source,
        similarity=0.20,
    )

    with pytest.raises(AppError) as exc_info:
        await service.merge(
            target_id=10,
            source_id=11,
            target_lock_version=2,
            current_user=CurrentUser(
                id=7,
                role=UserRole.QA,
            ),
        )

    assert exc_info.value.code == ErrorCode.CONFLICT
    assert exc_info.value.status_code == 409
    test_cases.save.assert_not_awaited()
    versions.create_snapshot.assert_not_awaited()
    audits.create.assert_not_awaited()
    session.commit.assert_not_awaited()
