# Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.audit.repository import AuditLogRepository
from app.common.auth_context import CurrentUser
from app.common.constants import AuditAction, ErrorCode, Priority, TestCaseStatus, UserRole
from app.common.exceptions import AppError
from app.testcases.models import TestCase
from app.testcases.query_service import TestCaseQueryService
from app.testcases.repository import TestCaseRepository
from app.testcases.snapshot import build_test_case_snapshot
from app.testcases.version_models import TestCaseVersion
from app.testcases.version_repository import TestCaseVersionRepository


class TestCaseVersionService:
    _RESTORE_ROLES = {UserRole.QA, UserRole.MANAGER}
    _RESTORABLE_FIELDS = (
        "summary",
        "preconditions",
        "steps",
        "expected_result",
        "priority",
        "test_techniques",
        "tags",
        "review_note",
    )

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
        self._query = TestCaseQueryService(test_cases)

    async def list_versions(
        self,
        test_case_id: int,
        current_user: CurrentUser,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[TestCaseVersion], int]:
        """List immutable test case versions after record-level authorization.

        Args:
            test_case_id: Test case identifier.
            current_user: Authenticated user requesting history.
            offset: Database row offset.
            limit: Maximum rows to return.

        Returns:
            Version rows and total count.

        Raises:
            AppError: When the test case is missing or inaccessible.
        """
        await self._query.get_test_case(test_case_id, current_user)
        items = await self._versions.list_for_test_case(test_case_id, offset=offset, limit=limit)
        total = await self._versions.count_for_test_case(test_case_id)
        return items, total

    async def compare_versions(
        self,
        test_case_id: int,
        from_version: int,
        to_version: int,
        current_user: CurrentUser,
    ) -> tuple[TestCaseVersion, TestCaseVersion, dict[str, dict[str, object]]]:
        """Compare two saved snapshots and return only changed fields.

        Args:
            test_case_id: Test case identifier.
            from_version: Earlier version number.
            to_version: Later version number.
            current_user: Authenticated user requesting comparison.

        Returns:
            Both versions and a field-level difference mapping.

        Raises:
            AppError: When the record or either version cannot be accessed.
        """
        await self._query.get_test_case(test_case_id, current_user)
        first = await self._get_version(test_case_id, from_version)
        second = await self._get_version(test_case_id, to_version)
        changes = self._build_changes(first.snapshot, second.snapshot)
        return first, second, changes

    async def restore_version(
        self,
        test_case_id: int,
        version_number: int,
        lock_version: int,
        current_user: CurrentUser,
    ) -> TestCase:
        """Restore historical content as NEEDS_FIX with version and audit evidence.

        Args:
            test_case_id: Test case identifier.
            version_number: Historical version to restore.
            lock_version: Client-side optimistic lock version.
            current_user: Authenticated QA or manager.

        Returns:
            The restored test case in NEEDS_FIX state.

        Raises:
            AppError: When access, version lookup, or optimistic locking fails.
        """
        test_case = await self._get_restore_target(test_case_id, current_user)
        if test_case.lock_version != lock_version:
            raise AppError(ErrorCode.CONFLICT, "Test case đã thay đổi. Vui lòng tải lại dữ liệu.", 409)
        version = await self._get_version(test_case_id, version_number)
        before = build_test_case_snapshot(test_case)
        self._apply_snapshot(test_case, version.snapshot)
        test_case.status = TestCaseStatus.NEEDS_FIX
        test_case.lock_version += 1
        await self._test_cases.clear_embedding(test_case.id)
        await self._test_cases.save(test_case)
        after = build_test_case_snapshot(test_case)
        await self._record_restore(test_case, current_user, before, after)
        await self._session.commit()
        return test_case

    async def _get_restore_target(self, test_case_id: int, current_user: CurrentUser) -> TestCase:
        test_case = await self._test_cases.get_by_id_for_update(test_case_id)
        if test_case is None:
            raise AppError(ErrorCode.TEST_CASE_NOT_FOUND, "Không tìm thấy test case.", 404)
        if current_user.role not in self._RESTORE_ROLES:
            raise AppError(ErrorCode.FORBIDDEN_ROLE, "Vai trò hiện tại không có quyền khôi phục test case.", 403)
        if current_user.role == UserRole.QA and test_case.created_by != current_user.id:
            raise AppError(ErrorCode.FORBIDDEN_RECORD, "Bạn không có quyền khôi phục test case này.", 403)
        return test_case

    async def _get_version(self, test_case_id: int, version_number: int) -> TestCaseVersion:
        version = await self._versions.get_by_number(test_case_id, version_number)
        if version is None:
            raise AppError(ErrorCode.TEST_CASE_VERSION_NOT_FOUND, "Không tìm thấy phiên bản test case.", 404)
        return version

    @classmethod
    def _apply_snapshot(cls, test_case: TestCase, snapshot: dict) -> None:
        for field_name in cls._RESTORABLE_FIELDS:
            if field_name not in snapshot:
                continue
            value = snapshot[field_name]
            if field_name == "priority":
                value = Priority(value)
            setattr(test_case, field_name, value)

    async def _record_restore(
        self,
        test_case: TestCase,
        current_user: CurrentUser,
        before: dict,
        after: dict,
    ) -> None:
        await self._versions.create_snapshot(test_case_id=test_case.id, snapshot=after, created_by=current_user.id)
        await self._audits.create(
            AuditLog(
                user_id=current_user.id,
                action=AuditAction.RESTORE_TEST_CASE,
                entity_type="test_case",
                entity_id=test_case.id,
                before_state=before,
                after_state=after,
            )
        )

    @staticmethod
    def _build_changes(before: dict, after: dict) -> dict[str, dict[str, object]]:
        keys = sorted(set(before) | set(after))
        return {
            key: {"from": before.get(key), "to": after.get(key)} for key in keys if before.get(key) != after.get(key)
        }
