# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.audit.repository import AuditLogRepository
from app.auth.schemas import CurrentUser
from app.common.ai.embedding_adapter import OpenAIEmbeddingAdapter
from app.common.ai.openai_adapter import OpenAIAdapter
from app.common.constants import AuditAction, ErrorCode, TestCaseStatus, UserRole
from app.common.exceptions import AppError
from app.requirements.repository import RequirementRepository
from app.testcases.models import TestCase
from app.testcases.repository import TestCaseRepository
from app.testcases.semantic_text import build_test_case_semantic_text
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
        embedding_adapter: OpenAIEmbeddingAdapter,
    ) -> None:
        self._session = session
        self._requirements = requirements
        self._test_cases = test_cases
        self._versions = versions
        self._audits = audits
        self._ai = ai_adapter
        self._embeddings = embedding_adapter

    async def generate_draft_test_cases(self, requirement_id: int, current_user: CurrentUser) -> list[TestCase]:
        """Generate validated DRAFT test cases, versions, audit evidence, and semantic vectors."""
        requirement = await self._requirements.get_by_id(requirement_id)
        if requirement is None:
            raise AppError(ErrorCode.REQUIREMENT_NOT_FOUND, "Không tìm thấy yêu cầu.", 404)
        self._require_requirement_access(requirement.created_by, current_user)

        generated = await self._ai.generate_test_cases(requirement.content, requirement.acceptance_criteria)
        test_cases = self._build_drafts(requirement, generated.data.test_cases, current_user.id)
        await self._test_cases.create_many(test_cases)
        embedding_tokens = await self._store_embeddings(test_cases)
        await self._store_versions(test_cases, current_user.id)
        await self._audit_generation(requirement.id, len(test_cases), current_user.id)
        await self._session.commit()
        self._log_generation(requirement.id, current_user.id, len(test_cases), generated.usage, embedding_tokens)
        return test_cases

    @staticmethod
    def _require_requirement_access(owner_id: int, current_user: CurrentUser) -> None:
        # SE-06 / BR-07: record-level permission prevents IDOR across QA users.
        if owner_id != current_user.id and current_user.role not in {UserRole.MANAGER, UserRole.ADMIN}:
            raise AppError(ErrorCode.FORBIDDEN_RECORD, "Bạn không có quyền truy cập yêu cầu này.", 403)

    @staticmethod
    def _build_drafts(requirement, generated_items, user_id: int) -> list[TestCase]:  # type: ignore[no-untyped-def]
        # BR-02/03/04: structured output is schema-valid and each DRAFT keeps requirement/module traceability.
        return [
            TestCase(
                requirement_id=requirement.id,
                module_id=requirement.module_id,
                summary=item.summary,
                preconditions=item.preconditions,
                steps=item.steps,
                expected_result=item.expected_result,
                priority=item.priority,
                test_techniques=item.test_techniques,
                review_note=item.review_note,
                status=TestCaseStatus.DRAFT,  # BR-01: AI output cannot skip human review/approval.
                lock_version=1,
                created_by=user_id,
            )
            for item in generated_items
        ]

    async def _store_embeddings(self, test_cases: list[TestCase]) -> int:
        # NC-05: embeddings are derived search data; failure must not invalidate otherwise valid generated DRAFTs.
        try:
            result = await self._embeddings.embed_texts([build_test_case_semantic_text(item) for item in test_cases])
        except AppError as exc:
            logger.warning(
                "Semantic embeddings deferred",
                extra={"error_code": exc.code.value, "operation": "embed_generated_test_cases"},
            )
            return 0
        pairs = [(item.id, vector) for item, vector in zip(test_cases, result.vectors, strict=True)]
        await self._test_cases.set_embeddings(pairs)
        return result.input_tokens

    async def _store_versions(self, test_cases: list[TestCase], user_id: int) -> None:
        # BR-06: the AI-produced DRAFT is version 1 before any human edit occurs.
        for test_case in test_cases:
            await self._versions.create_snapshot(
                test_case_id=test_case.id,
                snapshot=build_test_case_snapshot(test_case),
                created_by=user_id,
            )

    async def _audit_generation(self, requirement_id: int, count: int, user_id: int) -> None:
        # BR-06 / NC-11: every generation action is appended to audit history in the same transaction.
        await self._audits.create(
            AuditLog(
                user_id=user_id,
                action=AuditAction.GENERATE_TEST_CASES,
                entity_type="requirement",
                entity_id=requirement_id,
                before_state=None,
                after_state={"generated_count": count, "status": TestCaseStatus.DRAFT.value},
            )
        )

    @staticmethod
    def _log_generation(requirement_id: int, user_id: int, count: int, usage, embedding_tokens: int) -> None:
        # SE-15: token usage is logged without requirement content, API keys, or other sensitive data.
        logger.info(
            "Draft test cases generated",
            extra={
                "requirement_id": requirement_id,
                "user_id": user_id,
                "count": count,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "embedding_input_tokens": embedding_tokens,
                "operation": "generate_test_cases",
            },
        )
