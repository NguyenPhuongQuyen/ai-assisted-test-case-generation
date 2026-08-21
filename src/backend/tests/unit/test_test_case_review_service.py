# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.auth.schemas import CurrentUser
from app.common.constants import AuditAction, ErrorCode, Priority, UserRole
from app.common.constants import TestCaseStatus as CaseStatus
from app.common.exceptions import AppError
from app.testcases.review_service import TestCaseReviewService as ReviewService
from app.testcases.schemas import ReviewDecisionRequest
from app.testcases.schemas import TestCaseUpdateRequest as UpdateRequest


def make_case(*, status=CaseStatus.DRAFT, created_by=7, lock_version=2):
    return SimpleNamespace(
        id=10,
        requirement_id=2,
        module_id=3,
        summary="Add product to cart",
        preconditions=["User is signed in"],
        steps=["Add an in-stock product"],
        expected_result="Product is added",
        priority=Priority.HIGH,
        test_techniques=["equivalence_partitioning"],
        review_note=None,
        status=status,
        lock_version=lock_version,
        created_by=created_by,
    )


def build_service(record):
    session = SimpleNamespace(commit=AsyncMock())
    test_cases = SimpleNamespace(
        get_by_id_for_update=AsyncMock(return_value=record),
        save=AsyncMock(side_effect=lambda item: item),
    )
    versions = SimpleNamespace(create_snapshot=AsyncMock())
    audits = SimpleNamespace(create=AsyncMock())
    service = ReviewService(session, test_cases, versions, audits)
    return service, session, test_cases, versions, audits


@pytest.mark.asyncio
async def test_owner_can_edit_draft_and_records_version_and_audit() -> None:
    case = make_case()
    service, session, _, versions, audits = build_service(case)
    payload = UpdateRequest(lock_version=2, summary="Updated cart test case")

    result = await service.update_test_case(10, payload, CurrentUser(id=7, role=UserRole.QA))

    assert result.summary == "Updated cart test case"
    assert result.lock_version == 3
    versions.create_snapshot.assert_awaited_once()
    audit = audits.create.await_args.args[0]
    assert audit.action == AuditAction.EDIT_TEST_CASE
    assert audit.before_state["lock_version"] == 2
    assert audit.after_state["lock_version"] == 3
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_qa_cannot_edit_another_users_test_case() -> None:
    service, _, _, _, _ = build_service(make_case(created_by=99))

    with pytest.raises(AppError) as exc_info:
        await service.update_test_case(
            10,
            UpdateRequest(lock_version=2, summary="Updated summary"),
            CurrentUser(id=7, role=UserRole.QA),
        )

    assert exc_info.value.code == ErrorCode.FORBIDDEN_RECORD
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_admin_cannot_edit_test_case() -> None:
    service, _, _, _, _ = build_service(make_case(created_by=7))

    with pytest.raises(AppError) as exc_info:
        await service.update_test_case(
            10,
            UpdateRequest(lock_version=2, summary="Updated summary"),
            CurrentUser(id=1, role=UserRole.ADMIN),
        )

    assert exc_info.value.code == ErrorCode.FORBIDDEN_ROLE
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_stale_lock_version_is_rejected() -> None:
    service, _, test_cases, versions, audits = build_service(make_case(lock_version=4))

    with pytest.raises(AppError) as exc_info:
        await service.update_test_case(
            10,
            UpdateRequest(lock_version=3, summary="Stale edit"),
            CurrentUser(id=7, role=UserRole.QA),
        )

    assert exc_info.value.code == ErrorCode.CONFLICT
    assert exc_info.value.status_code == 409
    test_cases.save.assert_not_awaited()
    versions.create_snapshot.assert_not_awaited()
    audits.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_requires_at_least_one_mutable_field() -> None:
    service, _, _, _, _ = build_service(make_case())

    with pytest.raises(AppError) as exc_info:
        await service.update_test_case(
            10,
            UpdateRequest(lock_version=2),
            CurrentUser(id=7, role=UserRole.QA),
        )

    assert exc_info.value.code == ErrorCode.VALIDATION_ERROR
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_submit_review_moves_draft_to_in_review() -> None:
    case = make_case()
    service, _, _, _, audits = build_service(case)

    result = await service.submit_for_review(10, 2, CurrentUser(id=7, role=UserRole.QA))

    assert result.status == CaseStatus.IN_REVIEW
    assert result.lock_version == 3
    assert audits.create.await_args.args[0].action == AuditAction.SUBMIT_TEST_CASE_REVIEW


@pytest.mark.asyncio
async def test_approve_requires_in_review_status() -> None:
    service, _, _, _, _ = build_service(make_case(status=CaseStatus.DRAFT))

    with pytest.raises(AppError) as exc_info:
        await service.approve(
            10,
            ReviewDecisionRequest(lock_version=2),
            CurrentUser(id=7, role=UserRole.QA),
        )

    assert exc_info.value.code == ErrorCode.CONFLICT
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_approve_moves_in_review_to_approved() -> None:
    case = make_case(status=CaseStatus.IN_REVIEW)
    service, _, _, _, audits = build_service(case)

    result = await service.approve(
        10,
        ReviewDecisionRequest(lock_version=2, review_note="Reviewed and accepted"),
        CurrentUser(id=7, role=UserRole.QA),
    )

    assert result.status == CaseStatus.APPROVED
    assert result.review_note == "Reviewed and accepted"
    assert result.lock_version == 3
    assert audits.create.await_args.args[0].action == AuditAction.APPROVE_TEST_CASE


@pytest.mark.asyncio
async def test_manager_can_approve_another_users_test_case() -> None:
    service, _, _, _, _ = build_service(make_case(status=CaseStatus.IN_REVIEW, created_by=99))

    result = await service.approve(
        10,
        ReviewDecisionRequest(lock_version=2),
        CurrentUser(id=2, role=UserRole.MANAGER),
    )

    assert result.status == CaseStatus.APPROVED


@pytest.mark.asyncio
async def test_request_fix_requires_review_note() -> None:
    service, _, _, _, _ = build_service(make_case(status=CaseStatus.IN_REVIEW))

    with pytest.raises(AppError) as exc_info:
        await service.request_fix(
            10,
            ReviewDecisionRequest(lock_version=2),
            CurrentUser(id=7, role=UserRole.QA),
        )

    assert exc_info.value.code == ErrorCode.VALIDATION_ERROR
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_request_fix_moves_in_review_to_needs_fix() -> None:
    case = make_case(status=CaseStatus.IN_REVIEW)
    service, _, _, _, audits = build_service(case)

    result = await service.request_fix(
        10,
        ReviewDecisionRequest(lock_version=2, review_note="Add a boundary case"),
        CurrentUser(id=7, role=UserRole.QA),
    )

    assert result.status == CaseStatus.NEEDS_FIX
    assert result.review_note == "Add a boundary case"
    assert audits.create.await_args.args[0].action == AuditAction.REQUEST_TEST_CASE_FIX


@pytest.mark.asyncio
async def test_admin_cannot_approve_when_srs_limits_review_role() -> None:
    service, _, _, _, _ = build_service(make_case(status=CaseStatus.IN_REVIEW))

    with pytest.raises(AppError) as exc_info:
        await service.approve(
            10,
            ReviewDecisionRequest(lock_version=2),
            CurrentUser(id=1, role=UserRole.ADMIN),
        )

    assert exc_info.value.code == ErrorCode.FORBIDDEN_ROLE
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_reject_moves_in_review_to_rejected() -> None:
    case = make_case(status=CaseStatus.IN_REVIEW)
    service, _, _, _, audits = build_service(case)

    result = await service.reject(
        10,
        ReviewDecisionRequest(lock_version=2, review_note="Duplicate scenario"),
        CurrentUser(id=7, role=UserRole.QA),
    )

    assert result.status == CaseStatus.REJECTED
    assert result.review_note == "Duplicate scenario"
    assert audits.create.await_args.args[0].action == AuditAction.REJECT_TEST_CASE
