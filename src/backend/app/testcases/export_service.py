# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

import csv
from dataclasses import dataclass
from io import BytesIO, StringIO

from openpyxl import Workbook
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.audit.repository import AuditLogRepository
from app.auth.schemas import CurrentUser
from app.common.constants import AuditAction, ErrorCode, TestCaseExportFormat, TestCaseStatus, UserRole
from app.common.exceptions import AppError
from app.modules.repository import ModuleRepository
from app.testcases.models import TestCase
from app.testcases.repository import TestCaseRepository


@dataclass(frozen=True, slots=True)
class ExportedTestCaseFile:
    content: bytes
    media_type: str
    filename: str


class TestCaseExportService:
    _EXPORT_ROLES = {UserRole.QA, UserRole.MANAGER}
    _HEADERS = (
        "id",
        "requirement_id",
        "module_id",
        "summary",
        "preconditions",
        "steps",
        "expected_result",
        "priority",
        "test_techniques",
        "review_note",
        "status",
        "created_by",
        "created_at",
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
        """Export approved test cases for one module after role and record authorization.

        Args:
            module_id: Module whose approved test cases are exported.
            export_format: CSV or XLSX output format.
            current_user: Authenticated QA or manager requesting the export.

        Returns:
            In-memory file content plus response metadata.

        Raises:
            AppError: When role, module, or exportable data validation fails.
        """
        self._require_export_role(current_user)
        if await self._modules.get_by_id(module_id) is None:
            raise AppError(ErrorCode.MODULE_NOT_FOUND, "Không tìm thấy module đã chọn.", 404)

        # BR-05 / BR-07: QA exports only owned APPROVED records; managers may export the module-wide approved set.
        owner_id = current_user.id if current_user.role == UserRole.QA else None
        test_cases = await self._test_cases.list_approved_for_export(module_id=module_id, owner_id=owner_id)
        if not test_cases:
            raise AppError(ErrorCode.VALIDATION_ERROR, "Không có test case APPROVED để export.", 422)
        self._validate_approved_records(test_cases)

        exported_file = self._build_file(module_id, export_format, test_cases)
        # BR-06 / NC-11: export is auditable even though it does not mutate test-case content or status.
        await self._record_export(module_id, export_format, current_user, test_cases)
        await self._session.commit()
        return exported_file

    @staticmethod
    def _validate_approved_records(test_cases: list[TestCase]) -> None:
        # BR-01 / BR-05: export must never leak DRAFT, IN_REVIEW, NEEDS_FIX, EXPORTED, or REJECTED records.
        if any(test_case.status != TestCaseStatus.APPROVED for test_case in test_cases):
            raise AppError(ErrorCode.CONFLICT, "Chỉ test case APPROVED mới được export.", 409)

    def _require_export_role(self, current_user: CurrentUser) -> None:
        if current_user.role not in self._EXPORT_ROLES:
            raise AppError(ErrorCode.FORBIDDEN_ROLE, "Vai trò hiện tại không có quyền export test case.", 403)

    def _build_file(
        self,
        module_id: int,
        export_format: TestCaseExportFormat,
        test_cases: list[TestCase],
    ) -> ExportedTestCaseFile:
        rows = [self._to_row(test_case) for test_case in test_cases]
        if export_format == TestCaseExportFormat.CSV:
            return ExportedTestCaseFile(
                content=self._build_csv(rows),
                media_type="text/csv; charset=utf-8",
                filename=f"test-cases-module-{module_id}.csv",
            )
        return ExportedTestCaseFile(
            content=self._build_xlsx(rows),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"test-cases-module-{module_id}.xlsx",
        )

    async def _record_export(
        self,
        module_id: int,
        export_format: TestCaseExportFormat,
        current_user: CurrentUser,
        test_cases: list[TestCase],
    ) -> None:
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

    @classmethod
    def _build_csv(cls, rows: list[list[str | int]]) -> bytes:
        stream = StringIO(newline="")
        writer = csv.writer(stream)
        writer.writerow(cls._HEADERS)
        writer.writerows(rows)
        return stream.getvalue().encode("utf-8-sig")

    @classmethod
    def _build_xlsx(cls, rows: list[list[str | int]]) -> bytes:
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Test Cases"
        worksheet.append(cls._HEADERS)
        for row in rows:
            worksheet.append(row)
        stream = BytesIO()
        workbook.save(stream)
        return stream.getvalue()

    @classmethod
    def _to_row(cls, test_case: TestCase) -> list[str | int]:
        return [
            test_case.id,
            test_case.requirement_id,
            test_case.module_id,
            cls._safe_cell(test_case.summary),
            cls._safe_cell(cls._join_lines(test_case.preconditions)),
            cls._safe_cell(cls._join_numbered_steps(test_case.steps)),
            cls._safe_cell(test_case.expected_result),
            test_case.priority.value,
            cls._safe_cell(", ".join(test_case.test_techniques)),
            cls._safe_cell(test_case.review_note or ""),
            test_case.status.value,
            test_case.created_by,
            test_case.created_at.isoformat(),
        ]

    @staticmethod
    def _join_lines(values: list[str]) -> str:
        return "\n".join(values)

    @staticmethod
    def _join_numbered_steps(values: list[str]) -> str:
        return "\n".join(f"{index}. {value}" for index, value in enumerate(values, start=1))

    @staticmethod
    def _safe_cell(value: str) -> str:
        # Security: prevent spreadsheet formula execution when user-controlled text starts with a formula prefix.
        if value.startswith(("=", "+", "-", "@")):
            return "'" + value
        return value
