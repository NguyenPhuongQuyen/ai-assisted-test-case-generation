# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

from app.auth.schemas import CurrentUser
from app.common.constants import ErrorCode, TestCaseStatus, UserRole
from app.common.exceptions import AppError
from app.testcases.models import TestCase
from app.testcases.repository import TestCaseRepository


class TestCaseQueryService:
    def __init__(self, test_cases: TestCaseRepository) -> None:
        self._test_cases = test_cases

    async def list_test_cases(
        self,
        current_user: CurrentUser,
        *,
        requirement_id: int | None,
        case_status: TestCaseStatus | None,
        offset: int,
        limit: int,
    ) -> tuple[list[TestCase], int]:
        """List test cases available to the current user for the review screen.

        Args:
            current_user: Authenticated user requesting the list.
            requirement_id: Optional source-requirement filter.
            case_status: Optional test-case status filter.
            offset: Database row offset calculated from the requested page.
            limit: Maximum rows returned for the requested page.

        Returns:
            A tuple containing accessible test cases and the total matching row count.
        """
        # BR-07 / SE-06: QA users can browse only their own records; managers and admins can browse all records.
        owner_id = current_user.id if current_user.role == UserRole.QA else None
        filters = {
            "owner_id": owner_id,
            "requirement_id": requirement_id,
            "case_status": case_status,
        }
        items = await self._test_cases.list_accessible(offset=offset, limit=limit, **filters)
        total = await self._test_cases.count_accessible(**filters)
        return items, total

    async def get_test_case(self, test_case_id: int, current_user: CurrentUser) -> TestCase:
        """Return one test case after record-level authorization.

        Args:
            test_case_id: Test case identifier.
            current_user: Authenticated user requesting the record.

        Returns:
            The requested test case.

        Raises:
            AppError: When the test case is missing or the user cannot access the record.
        """
        test_case = await self._test_cases.get_by_id(test_case_id)
        if test_case is None:
            raise AppError(ErrorCode.TEST_CASE_NOT_FOUND, "Không tìm thấy test case.", 404)

        # BR-07 / SE-06: prevent direct object access to another QA user's test case.
        if test_case.created_by != current_user.id and current_user.role not in {UserRole.MANAGER, UserRole.ADMIN}:
            raise AppError(ErrorCode.FORBIDDEN_RECORD, "Bạn không có quyền truy cập test case này.", 403)

        return test_case
