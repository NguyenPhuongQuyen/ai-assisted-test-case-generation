# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.audit.repository import AuditLogRepository
from app.auth.schemas import CurrentUser
from app.common.constants import AuditAction, ErrorCode, TestCaseStatus, UserRole
from app.common.exceptions import AppError
from app.testcases.models import TestCase
from app.testcases.repository import TestCaseRepository
from app.testcases.schemas import ReviewDecisionRequest, TestCaseUpdateRequest
from app.testcases.snapshot import build_test_case_snapshot
from app.testcases.version_repository import TestCaseVersionRepository


class TestCaseReviewService:
    _EDITABLE_STATUSES = {TestCaseStatus.DRAFT, TestCaseStatus.IN_REVIEW, TestCaseStatus.NEEDS_FIX}
    _REVIEW_ROLES = {UserRole.QA, UserRole.MANAGER}

    def __init__(
        self,
        session: AsyncSession,
        test_cases: TestCaseRepository,
        versions: TestCaseVersionRepository,
        audits: AuditLogRepository,
    ) -> None:
        self._session = session
        self._test_cases = test_cases
        self._versions = versions
        self._audits = audits

    async def update_test_case(
        self, test_case_id: int, payload: TestCaseUpdateRequest, current_user: CurrentUser
    ) -> TestCase:
        """Edit a reviewable test case and persist version/audit history.

        Args:
            test_case_id: Test case identifier.
            payload: Validated mutable fields plus the expected lock version.
            current_user: Authenticated reviewer.

        Returns:
            The updated test case.

        Raises:
            AppError: When access, status, validation, or optimistic locking fails.
        """
        test_case = await self._get_accessible_for_update(test_case_id, current_user)
        self._require_review_role(current_user)
        self._require_lock_version(test_case, payload.lock_version)
        if test_case.status not in self._EDITABLE_STATUSES:
            raise self._conflict("Test case ở trạng thái hiện tại không thể chỉnh sửa.")

        changes = payload.model_dump(exclude_unset=True, exclude={"lock_version"})
        if not changes:
            raise AppError(ErrorCode.VALIDATION_ERROR, "Không có dữ liệu thay đổi.", 422)

        before = build_test_case_snapshot(test_case)
        for field_name, value in changes.items():
            setattr(test_case, field_name, value)
        self._validate_required_fields(test_case)
        await self._save_new_version(test_case)
        after = build_test_case_snapshot(test_case)

        # BR-06: each edit creates immutable version and append-only audit evidence.
        await self._record_change(test_case, current_user, AuditAction.EDIT_TEST_CASE, before, after)
        await self._session.commit()
        return test_case

    async def submit_for_review(self, test_case_id: int, lock_version: int, current_user: CurrentUser) -> TestCase:
        """Move DRAFT or NEEDS_FIX to IN_REVIEW after permission and field checks."""
        test_case = await self._get_accessible_for_update(test_case_id, current_user)
        self._require_review_role(current_user)
        self._require_lock_version(test_case, lock_version)
        if test_case.status not in {TestCaseStatus.DRAFT, TestCaseStatus.NEEDS_FIX}:
            raise self._conflict("Chỉ DRAFT hoặc NEEDS_FIX mới có thể gửi rà soát.")
        self._validate_required_fields(test_case)
        return await self._transition(
            test_case, current_user, TestCaseStatus.IN_REVIEW, AuditAction.SUBMIT_TEST_CASE_REVIEW
        )

    async def approve(self, test_case_id: int, payload: ReviewDecisionRequest, current_user: CurrentUser) -> TestCase:
        """Approve an IN_REVIEW test case for authorized QA or manager reviewers."""
        test_case = await self._get_accessible_for_update(test_case_id, current_user)
        self._require_review_role(current_user)
        self._require_lock_version(test_case, payload.lock_version)
        if test_case.status != TestCaseStatus.IN_REVIEW:
            # BR-01 / BR-05: DRAFT cannot bypass human review and approval permission.
            raise self._conflict("Chỉ test case IN_REVIEW mới có thể được duyệt.")
        self._validate_required_fields(test_case)
        if payload.review_note is not None:
            test_case.review_note = payload.review_note
        return await self._transition(test_case, current_user, TestCaseStatus.APPROVED, AuditAction.APPROVE_TEST_CASE)

    async def request_fix(
        self, test_case_id: int, payload: ReviewDecisionRequest, current_user: CurrentUser
    ) -> TestCase:
        """Return an IN_REVIEW test case to NEEDS_FIX and record the review note."""
        test_case = await self._get_accessible_for_update(test_case_id, current_user)
        self._require_review_role(current_user)
        self._require_lock_version(test_case, payload.lock_version)
        if test_case.status != TestCaseStatus.IN_REVIEW:
            raise self._conflict("Chỉ test case IN_REVIEW mới có thể yêu cầu chỉnh sửa.")
        if not payload.review_note:
            raise AppError(ErrorCode.VALIDATION_ERROR, "Cần ghi lý do yêu cầu chỉnh sửa.", 422)
        test_case.review_note = payload.review_note
        return await self._transition(
            test_case, current_user, TestCaseStatus.NEEDS_FIX, AuditAction.REQUEST_TEST_CASE_FIX
        )

    async def reject(self, test_case_id: int, payload: ReviewDecisionRequest, current_user: CurrentUser) -> TestCase:
        """Reject a DRAFT or IN_REVIEW test case and keep version/audit evidence."""
        test_case = await self._get_accessible_for_update(test_case_id, current_user)
        self._require_review_role(current_user)
        self._require_lock_version(test_case, payload.lock_version)
        if test_case.status not in {TestCaseStatus.DRAFT, TestCaseStatus.IN_REVIEW}:
            raise self._conflict("Trạng thái hiện tại không cho phép từ chối test case.")
        if payload.review_note is not None:
            test_case.review_note = payload.review_note
        return await self._transition(test_case, current_user, TestCaseStatus.REJECTED, AuditAction.REJECT_TEST_CASE)

    async def _get_accessible_for_update(self, test_case_id: int, current_user: CurrentUser) -> TestCase:
        test_case = await self._test_cases.get_by_id_for_update(test_case_id)
        if test_case is None:
            raise AppError(ErrorCode.TEST_CASE_NOT_FOUND, "Không tìm thấy test case.", 404)
        # BR-07 / SE-06: QA users may mutate only their own records; managers may review team records.
        if test_case.created_by != current_user.id and current_user.role not in {UserRole.MANAGER, UserRole.ADMIN}:
            raise AppError(ErrorCode.FORBIDDEN_RECORD, "Bạn không có quyền thao tác test case này.", 403)
        return test_case

    def _require_review_role(self, current_user: CurrentUser) -> None:
        # BR-05: only the roles defined by the SRS as reviewers may review or approve test cases.
        if current_user.role not in self._REVIEW_ROLES:
            raise AppError(ErrorCode.FORBIDDEN_ROLE, "Vai trò hiện tại không có quyền rà soát test case.", 403)

    @staticmethod
    def _require_lock_version(test_case: TestCase, expected_version: int) -> None:
        # DB-15: reject stale client state before any write so one reviewer cannot overwrite another reviewer.
        if test_case.lock_version != expected_version:
            raise AppError(ErrorCode.CONFLICT, "Test case đã thay đổi. Vui lòng tải lại dữ liệu.", 409)

    async def _save_new_version(self, test_case: TestCase) -> None:
        test_case.lock_version += 1
        await self._test_cases.save(test_case)

    async def _transition(
        self,
        test_case: TestCase,
        current_user: CurrentUser,
        target_status: TestCaseStatus,
        action: AuditAction,
    ) -> TestCase:
        before = build_test_case_snapshot(test_case)
        test_case.status = target_status
        await self._save_new_version(test_case)
        after = build_test_case_snapshot(test_case)
        await self._record_change(test_case, current_user, action, before, after)
        await self._session.commit()
        return test_case

    async def _record_change(
        self,
        test_case: TestCase,
        current_user: CurrentUser,
        action: AuditAction,
        before: dict,
        after: dict,
    ) -> None:
        await self._versions.create_snapshot(
            test_case_id=test_case.id,
            snapshot=after,
            created_by=current_user.id,
        )
        await self._audits.create(
            AuditLog(
                user_id=current_user.id,
                action=action,
                entity_type="test_case",
                entity_id=test_case.id,
                before_state=before,
                after_state=after,
            )
        )

    @staticmethod
    def _validate_required_fields(test_case: TestCase) -> None:
        # BR-02 / BR-03: review decisions require mandatory content, priority, and source traceability.
        if not test_case.summary or not test_case.steps or not test_case.expected_result or test_case.priority is None:
            raise AppError(ErrorCode.VALIDATION_ERROR, "Test case thiếu trường bắt buộc.", 422)
        if not test_case.requirement_id or not test_case.module_id:
            raise AppError(ErrorCode.VALIDATION_ERROR, "Test case thiếu liên kết truy vết nguồn.", 422)

    @staticmethod
    def _conflict(message: str) -> AppError:
        return AppError(ErrorCode.CONFLICT, message, 409)
