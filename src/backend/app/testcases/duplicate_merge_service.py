# Source assistance: OpenAI ChatGPT, 2026-08-25 (AI-05).

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.audit.repository import AuditLogRepository
from app.common.auth_context import CurrentUser
from app.common.config import get_settings
from app.common.constants import (
    AuditAction,
    ErrorCode,
    Priority,
    TestCaseStatus,
    UserRole,
)
from app.common.exceptions import AppError
from app.testcases.models import TestCase
from app.testcases.repository import TestCaseRepository
from app.testcases.snapshot import build_test_case_snapshot
from app.testcases.version_repository import TestCaseVersionRepository


class DuplicateMergeService:
    """Keep a canonical test case and retire a confirmed duplicate."""

    _MERGE_ROLES = {UserRole.QA, UserRole.MANAGER}
    _MERGEABLE_STATUSES = {
        TestCaseStatus.DRAFT,
        TestCaseStatus.IN_REVIEW,
        TestCaseStatus.NEEDS_FIX,
    }
    _PRIORITY_RANK = {
        Priority.LOW: 0,
        Priority.MEDIUM: 1,
        Priority.HIGH: 2,
    }

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
        self._threshold = get_settings().duplicate_similarity_threshold

    async def merge(
        self,
        *,
        target_id: int,
        source_id: int,
        target_lock_version: int,
        current_user: CurrentUser,
    ) -> tuple[TestCase, int, float]:
        self._require_role(current_user)

        if target_id == source_id:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "Không thể gộp một test case với chính nó.",
                422,
            )

        target = await self._get_accessible_for_update(
            target_id,
            current_user,
        )
        self._require_lock_version(
            target,
            target_lock_version,
        )

        source = await self._get_accessible_for_update(
            source_id,
            current_user,
        )

        self._require_mergeable(target)
        self._require_mergeable(source)
        self._require_same_module(target, source)

        similarity = await self._test_cases.get_duplicate_similarity(
            target_id=target.id,
            source_id=source.id,
        )

        if similarity is None or similarity < self._threshold:
            raise AppError(
                ErrorCode.CONFLICT,
                ("Hai test case không còn đạt ngưỡng duplicate. Vui lòng kiểm tra lại."),
                409,
            )

        target_before = build_test_case_snapshot(target)
        source_before = build_test_case_snapshot(source)

        self._apply_canonical_merge(
            target,
            source,
            similarity,
        )

        target.lock_version += 1
        source.lock_version += 1

        await self._test_cases.clear_embedding(target.id)
        await self._test_cases.clear_embedding(source.id)
        await self._test_cases.save(target)
        await self._test_cases.save(source)

        target_after = build_test_case_snapshot(target)
        source_after = build_test_case_snapshot(source)

        await self._record_versions(
            target,
            source,
            target_after,
            source_after,
            current_user,
        )
        await self._record_audits(
            target,
            source,
            target_before,
            target_after,
            source_before,
            source_after,
            current_user,
        )

        await self._session.commit()
        return target, source.id, similarity

    async def _get_accessible_for_update(
        self,
        test_case_id: int,
        current_user: CurrentUser,
    ) -> TestCase:
        test_case = await self._test_cases.get_by_id_for_update(test_case_id)

        if test_case is None:
            raise AppError(
                ErrorCode.TEST_CASE_NOT_FOUND,
                "Không tìm thấy test case.",
                404,
            )

        if current_user.role == UserRole.QA and test_case.created_by != current_user.id:
            raise AppError(
                ErrorCode.FORBIDDEN_RECORD,
                "Bạn không có quyền gộp test case này.",
                403,
            )

        return test_case

    def _require_role(
        self,
        current_user: CurrentUser,
    ) -> None:
        if current_user.role not in self._MERGE_ROLES:
            raise AppError(
                ErrorCode.FORBIDDEN_ROLE,
                "Vai trò hiện tại không có quyền gộp test case.",
                403,
            )

    @staticmethod
    def _require_lock_version(
        target: TestCase,
        expected_version: int,
    ) -> None:
        if target.lock_version != expected_version:
            raise AppError(
                ErrorCode.CONFLICT,
                ("Test case đích đã thay đổi. Vui lòng tải lại dữ liệu."),
                409,
            )

    def _require_mergeable(
        self,
        test_case: TestCase,
    ) -> None:
        if test_case.status not in self._MERGEABLE_STATUSES:
            raise AppError(
                ErrorCode.CONFLICT,
                ("Chỉ test case đang trong luồng rà soát mới có thể được gộp."),
                409,
            )

    @staticmethod
    def _require_same_module(
        target: TestCase,
        source: TestCase,
    ) -> None:
        if target.module_id != source.module_id:
            raise AppError(
                ErrorCode.CONFLICT,
                "Chỉ có thể gộp test case trong cùng module.",
                409,
            )

    def _apply_canonical_merge(
        self,
        target: TestCase,
        source: TestCase,
        similarity: float,
    ) -> None:
        if self._PRIORITY_RANK[source.priority] > self._PRIORITY_RANK[target.priority]:
            target.priority = source.priority

        if target.status != TestCaseStatus.DRAFT:
            target.status = TestCaseStatus.NEEDS_FIX

        target.review_note = self._append_note(
            target.review_note,
            (f"Đã gộp duplicate TC #{source.id} - {source.summary} (similarity {similarity:.2%})."),
        )

        source.status = TestCaseStatus.REJECTED
        source.review_note = self._append_note(
            source.review_note,
            f"Đã gộp vào TC #{target.id}.",
        )

    @staticmethod
    def _append_note(
        existing: str | None,
        note: str,
    ) -> str:
        if not existing:
            return note[:1000]

        available = 1000 - len(note) - 1
        if available <= 0:
            return note[:1000]

        return f"{existing[:available]}\n{note}"

    async def _record_versions(
        self,
        target: TestCase,
        source: TestCase,
        target_after: dict,
        source_after: dict,
        current_user: CurrentUser,
    ) -> None:
        await self._versions.create_snapshot(
            test_case_id=target.id,
            snapshot=target_after,
            created_by=current_user.id,
        )
        await self._versions.create_snapshot(
            test_case_id=source.id,
            snapshot=source_after,
            created_by=current_user.id,
        )

    async def _record_audits(
        self,
        target: TestCase,
        source: TestCase,
        target_before: dict,
        target_after: dict,
        source_before: dict,
        source_after: dict,
        current_user: CurrentUser,
    ) -> None:
        await self._audits.create(
            AuditLog(
                user_id=current_user.id,
                action=AuditAction.EDIT_TEST_CASE,
                entity_type="test_case",
                entity_id=target.id,
                before_state=target_before,
                after_state={
                    **target_after,
                    "merged_from_test_case_id": source.id,
                },
            )
        )

        await self._audits.create(
            AuditLog(
                user_id=current_user.id,
                action=AuditAction.REJECT_TEST_CASE,
                entity_type="test_case",
                entity_id=source.id,
                before_state=source_before,
                after_state={
                    **source_after,
                    "merged_into_test_case_id": target.id,
                },
            )
        )
