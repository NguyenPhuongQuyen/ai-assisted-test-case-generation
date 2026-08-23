# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.auth.schemas import CurrentUser
from app.common.ai.embedding_adapter import EmbeddingBatchResult
from app.common.constants import Priority, UserRole
from app.common.constants import TestCaseStatus as CaseStatus
from app.testcases.duplicate_service import DuplicateDetectionService
from app.testcases.repository import DuplicateCandidateRecord


def build_service(*, has_embedding: bool):
    target = SimpleNamespace(
        id=10,
        module_id=3,
        summary="Add product to cart",
        preconditions=["User is signed in"],
        steps=["Add an in-stock product"],
        expected_result="Product is added",
        created_by=7,
    )
    session = SimpleNamespace(commit=AsyncMock())
    repository = SimpleNamespace(
        has_embedding=AsyncMock(return_value=has_embedding),
        set_embedding=AsyncMock(),
        find_duplicate_candidates=AsyncMock(
            return_value=(
                [
                    DuplicateCandidateRecord(
                        id=11,
                        requirement_id=4,
                        summary="Add available item to cart",
                        status=CaseStatus.DRAFT,
                        priority=Priority.HIGH,
                        similarity=0.91,
                    )
                ],
                1,
            )
        ),
    )
    query_service = SimpleNamespace(get_test_case=AsyncMock(return_value=target))
    embedding_adapter = SimpleNamespace(
        embed_texts=AsyncMock(return_value=EmbeddingBatchResult(vectors=[[0.1] * 1536], input_tokens=12))
    )
    service = DuplicateDetectionService(session, repository, query_service, embedding_adapter)
    return service, session, repository, embedding_adapter


@pytest.mark.asyncio
async def test_qa_duplicate_search_is_limited_to_own_records() -> None:
    service, _, repository, embedding_adapter = build_service(has_embedding=True)

    candidates, total, threshold, model = await service.find_candidates(
        10,
        CurrentUser(id=7, role=UserRole.QA),
        offset=0,
        limit=5,
    )

    assert len(candidates) == 1
    assert total == 1
    assert candidates[0].similarity >= threshold
    assert model
    embedding_adapter.embed_texts.assert_not_awaited()
    repository.find_duplicate_candidates.assert_awaited_once_with(
        test_case_id=10,
        module_id=3,
        owner_id=7,
        threshold=threshold,
        offset=0,
        limit=5,
    )


@pytest.mark.asyncio
async def test_missing_embedding_is_created_before_similarity_query() -> None:
    service, session, repository, embedding_adapter = build_service(has_embedding=False)

    await service.find_candidates(
        10,
        CurrentUser(id=7, role=UserRole.QA),
        offset=0,
        limit=5,
    )

    embedding_adapter.embed_texts.assert_awaited_once()
    repository.set_embedding.assert_awaited_once()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_manager_duplicate_search_can_compare_team_records() -> None:
    service, _, repository, _ = build_service(has_embedding=True)

    _, total, threshold, _ = await service.find_candidates(
        10,
        CurrentUser(id=2, role=UserRole.MANAGER),
        offset=10,
        limit=10,
    )

    assert total == 1

    repository.find_duplicate_candidates.assert_awaited_once_with(
        test_case_id=10,
        module_id=3,
        owner_id=None,
        threshold=threshold,
        offset=10,
        limit=10,
    )
