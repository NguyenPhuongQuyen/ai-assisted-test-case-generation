# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.ai.embedding_adapter import OpenAIEmbeddingAdapter
from app.common.auth_context import CurrentUser
from app.common.config import get_settings
from app.common.constants import UserRole
from app.testcases.query_service import TestCaseQueryService
from app.testcases.repository import DuplicateCandidateRecord, TestCaseRepository
from app.testcases.semantic_text import build_test_case_semantic_text

logger = logging.getLogger(__name__)


class DuplicateDetectionService:
    def __init__(
        self,
        session: AsyncSession,
        test_cases: TestCaseRepository,
        query_service: TestCaseQueryService,
        embedding_adapter: OpenAIEmbeddingAdapter,
    ) -> None:
        self._session = session
        self._test_cases = test_cases
        self._query_service = query_service
        self._embeddings = embedding_adapter
        settings = get_settings()
        self._threshold = settings.duplicate_similarity_threshold
        self._embedding_model = settings.openai_embedding_model

    async def find_candidates(
        self,
        test_case_id: int,
        current_user: CurrentUser,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[DuplicateCandidateRecord], int, float, str]:
        """Return a paginated list of visible semantic duplicate candidates.

        Args:
            test_case_id: Test case used as the similarity target.
            current_user: Authenticated user requesting candidates.
            offset: Number of matching candidates to skip.
            limit: Maximum candidates returned in the current page.

        Returns:
            Candidates, total match count, threshold, and embedding model.

        Raises:
            AppError: When the target is missing, forbidden, or embedding fails.
        """
        target = await self._query_service.get_test_case(
            test_case_id,
            current_user,
        )
        if not await self._test_cases.has_embedding(target.id):
            await self._embed_and_store(target)

        owner_id = current_user.id if current_user.role == UserRole.QA else None
        candidates, total = await self._test_cases.find_duplicate_candidates(
            test_case_id=target.id,
            module_id=target.module_id,
            owner_id=owner_id,
            threshold=self._threshold,
            offset=offset,
            limit=limit,
        )
        return (
            candidates,
            total,
            self._threshold,
            self._embedding_model,
        )

    async def _embed_and_store(self, test_case) -> None:  # type: ignore[no-untyped-def]
        result = await self._embeddings.embed_texts([build_test_case_semantic_text(test_case)])
        await self._test_cases.set_embedding(test_case.id, result.vectors[0])
        await self._session.commit()
        logger.info(
            "Test case embedding stored",
            extra={
                "test_case_id": test_case.id,
                "user_id": test_case.created_by,
                "input_tokens": result.input_tokens,
                "operation": "embed_test_case",
            },
        )
