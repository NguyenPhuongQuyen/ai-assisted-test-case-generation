import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.audit.repository import AuditLogRepository
from app.auth.schemas import CurrentUser
from app.common.ai.openai_adapter import OpenAIAdapter
from app.common.constants import AuditAction, ErrorCode, TestCaseStatus, UserRole
from app.common.exceptions import AppError
from app.requirements.repository import RequirementRepository
from app.testcases.models import TestCase
from app.testcases.repository import TestCaseRepository
from app.testcases.snapshot import build_test_case_snapshot
from app.testcases.version_repository import TestCaseVersionRepository

logger = logging.getLogger(__name__)


class TestCaseGenerationService:
    def __init__(
        self,
        session: AsyncSession,
        requirements: RequirementRepository,
        test_cases: TestCaseRepository,
        versions: TestCaseVersionRepository,
        audits: AuditLogRepository,
        ai_adapter: OpenAIAdapter,
    ) -> None:
        self._session = session
        self._requirements = requirements
        self._test_cases = test_cases
        self._versions = versions
        self._audits = audits
        self._ai = ai_adapter

    async def generate_draft_test_cases(self, requirement_id: int, current_user: CurrentUser) -> list[TestCase]:
        """Generate structured test cases and persist them only as DRAFT after permission/schema checks."""
        requirement = await self._requirements.get_by_id(requirement_id)
        if requirement is None:
            raise AppError(ErrorCode.REQUIREMENT_NOT_FOUND, "Không tìm thấy yêu cầu.", 404)

        # SE-06 / BR-07: record-level permission prevents IDOR across QA users.
        if requirement.created_by != current_user.id and current_user.role not in {UserRole.MANAGER, UserRole.ADMIN}:
            raise AppError(ErrorCode.FORBIDDEN_RECORD, "Bạn không có quyền truy cập yêu cầu này.", 403)

        generated = await self._ai.generate_test_cases(requirement.content, requirement.acceptance_criteria)

        # BR-02: Structured Output + Pydantic guarantees required fields before persistence.
        # BR-04: invalid schema is rejected inside the AI adapter and must never be persisted.
        test_cases = [
            TestCase(
                requirement_id=requirement.id,
                module_id=requirement.module_id,  # BR-03: trace each test case to source requirement and module.
                summary=item.summary,
                preconditions=item.preconditions,
                steps=item.steps,
                expected_result=item.expected_result,
                priority=item.priority,
                test_techniques=item.test_techniques,
                review_note=item.review_note,
                status=TestCaseStatus.DRAFT,  # BR-01: AI output cannot skip human review/approval.
                lock_version=1,
                created_by=current_user.id,
            )
            for item in generated.data.test_cases
        ]
        await self._test_cases.create_many(test_cases)

        # BR-06: the AI-produced DRAFT is version 1 before any human edit occurs.
        for test_case in test_cases:
            await self._versions.create_snapshot(
                test_case_id=test_case.id,
                snapshot=build_test_case_snapshot(test_case),
                created_by=current_user.id,
            )

        # BR-06 / NC-11: every generation action is appended to the audit trail in the same transaction.
        await self._audits.create(
            AuditLog(
                user_id=current_user.id,
                action=AuditAction.GENERATE_TEST_CASES,
                entity_type="requirement",
                entity_id=requirement.id,
                before_state=None,
                after_state={"generated_count": len(test_cases), "status": TestCaseStatus.DRAFT.value},
            )
        )
        await self._session.commit()

        # SE-15: log token counts, but never log requirement body, API key, token or other sensitive content.
        logger.info(
            "Draft test cases generated",
            extra={
                "requirement_id": requirement.id,
                "user_id": current_user.id,
                "count": len(test_cases),
                "input_tokens": generated.usage.input_tokens,
                "output_tokens": generated.usage.output_tokens,
                "operation": "generate_test_cases",
            },
        )
        return test_cases
