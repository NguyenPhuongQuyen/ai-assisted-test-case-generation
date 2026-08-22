# Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.audit.repository import AuditLogRepository
from app.auth.schemas import CurrentUser
from app.common.constants import (
    AuditAction,
    ErrorCode,
    TestCaseExportFormat,
    TestCaseStatus,
    UserRole,
)
from app.common.exceptions import AppError
from app.modules.repository import ModuleRepository
from app.testcases.csv_exporter import build_csv
from app.testcases.export_rows import to_export_row
from app.testcases.models import TestCase
from app.testcases.repository import TestCaseRepository
from app.testcases.xlsx_exporter import build_xlsx


@dataclass(frozen=True, slots=True)
class ExportedTestCaseFile:
    content: bytes
    media_type: str
    filename: str


class TestCaseExportService:
    _EXPORT_ROLES = {
        UserRole.QA,
        UserRole.MANAGER,
    }

    _DISPLAY_HEADERS = (
        "ID",
        "Requirement ID",
        "Module ID",
        "Summary",
        "Preconditions",
        "Steps",
        "Expected Result",
        "Priority",
        "Test Techniques",
        "Review Note",
        "Status",
        "Created By",
        "Created At",
    )

    def __init__(
        self,
        session: AsyncSession,
        test_cases: TestCaseRepository,
        modules: ModuleRepository,
        audits: AuditLogRepository,
    ) -> None:
        self._session = session
        self._test_cases = test_cases
        self._modules = modules
        self._audits = audits

    async def export_approved_test_cases(
        self,
        module_id: int,
        export_format: TestCaseExportFormat,
        current_user: CurrentUser,
    ) -> ExportedTestCaseFile:
        """Export approved test cases after authorization."""
        self._require_export_role(current_user)

        test_cases = await self._load_approved_test_cases(
            module_id,
            current_user,
        )
        self._validate_approved_records(test_cases)

        exported_file = self._build_file(
            module_id,
            export_format,
            test_cases,
        )

        self._mark_exported(test_cases)

        await self._record_export(
            module_id,
            export_format,
            current_user,
            test_cases,
        )
        await self._session.commit()

        return exported_file

    async def _load_approved_test_cases(
        self,
        module_id: int,
        current_user: CurrentUser,
    ) -> list[TestCase]:
        if await self._modules.get_by_id(module_id) is None:
            raise AppError(
                ErrorCode.MODULE_NOT_FOUND,
                "Không tìm thấy module đã chọn.",
                404,
            )

        # BR-05 / BR-07:
        # QA exports only owned APPROVED records.
        owner_id = current_user.id if current_user.role == UserRole.QA else None

        test_cases = await self._test_cases.list_approved_for_export(
            module_id=module_id,
            owner_id=owner_id,
        )

        if not test_cases:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "Không có test case APPROVED để export.",
                422,
            )

        return test_cases

    @staticmethod
    def _validate_approved_records(
        test_cases: list[TestCase],
    ) -> None:
        # BR-01 / BR-05:
        # Never export records outside APPROVED state.
        if any(test_case.status != TestCaseStatus.APPROVED for test_case in test_cases):
            raise AppError(
                ErrorCode.CONFLICT,
                "Chỉ test case APPROVED mới được export.",
                409,
            )

    def _require_export_role(
        self,
        current_user: CurrentUser,
    ) -> None:
        if current_user.role not in self._EXPORT_ROLES:
            raise AppError(
                ErrorCode.FORBIDDEN_ROLE,
                "Vai trò hiện tại không có quyền export test case.",
                403,
            )

    def _build_file(
        self,
        module_id: int,
        export_format: TestCaseExportFormat,
        test_cases: list[TestCase],
    ) -> ExportedTestCaseFile:
        rows = [to_export_row(test_case) for test_case in test_cases]

        if export_format == TestCaseExportFormat.CSV:
            return ExportedTestCaseFile(
                content=build_csv(
                    rows,
                    self._DISPLAY_HEADERS,
                ),
                media_type="text/csv; charset=utf-8",
                filename=f"test-cases-module-{module_id}.csv",
            )

        return ExportedTestCaseFile(
            content=build_xlsx(
                module_id,
                rows,
                self._DISPLAY_HEADERS,
            ),
            media_type=("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            filename=f"test-cases-module-{module_id}.xlsx",
        )

    @staticmethod
    def _mark_exported(
        test_cases: list[TestCase],
    ) -> None:
        # BRD lifecycle:
        # APPROVED -> EXPORTED after successful artifact creation.
        for test_case in test_cases:
            test_case.status = TestCaseStatus.EXPORTED

    async def _record_export(
        self,
        module_id: int,
        export_format: TestCaseExportFormat,
        current_user: CurrentUser,
        test_cases: list[TestCase],
    ) -> None:
        # BR-06 / NC-11: export action is auditable.
        await self._audits.create(
            AuditLog(
                user_id=current_user.id,
                action=AuditAction.EXPORT_TEST_CASES,
                entity_type="test_case_export",
                entity_id=module_id,
                before_state=None,
                after_state={
                    "module_id": module_id,
                    "format": export_format.value,
                    "count": len(test_cases),
                    "test_case_ids": [test_case.id for test_case in test_cases],
                },
            )
        )
