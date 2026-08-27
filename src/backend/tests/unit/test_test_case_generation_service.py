from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.auth.schemas import CurrentUser
from app.common.ai.embedding_adapter import EmbeddingBatchResult
from app.common.ai.openai_adapter import AIUsage, GeneratedBatchResult, PromptRuntimeConfig
from app.common.constants import ErrorCode, Priority, UserRole
from app.common.constants import TestCaseStatus as CaseStatus
from app.common.exceptions import AppError
from app.testcases.schemas import GeneratedTestCase, GeneratedTestCaseBatch
from app.testcases.service import TestCaseGenerationService as GenerationService


def build_service(*, requirement: object | None, ai_result: object) -> tuple[GenerationService, object]:
    session = AsyncMock()
    requirements = SimpleNamespace(get_by_id=AsyncMock(return_value=requirement))
    test_cases = SimpleNamespace(
        create_many=AsyncMock(side_effect=lambda rows: rows),
        set_embeddings=AsyncMock(),
    )
    versions = SimpleNamespace(create_snapshots=AsyncMock())
    audits = SimpleNamespace(create=AsyncMock())
    prompt_config = SimpleNamespace(
        version_number=2,
        model_name="gpt-5",
        schema_version="test-case-v1",
        system_prompt="System prompt long enough for generation tests.",
        user_prompt_template="Requirement: {requirement_text}\nAcceptance Criteria: {acceptance_criteria}",
        max_output_tokens=4000,
    )
    prompts = SimpleNamespace(get_active=AsyncMock(return_value=prompt_config))
    ai_adapter = SimpleNamespace(
        generate_test_cases=AsyncMock(side_effect=ai_result if isinstance(ai_result, Exception) else None)
    )
    if not isinstance(ai_result, Exception):
        ai_adapter.generate_test_cases.return_value = ai_result
    embedding_adapter = SimpleNamespace(
        embed_texts=AsyncMock(return_value=EmbeddingBatchResult(vectors=[[0.1] * 1536], input_tokens=12))
    )
    service = GenerationService(
        session, requirements, test_cases, versions, audits, prompts, ai_adapter, embedding_adapter
    )
    collaborators = SimpleNamespace(
        session=session,
        requirements=requirements,
        test_cases=test_cases,
        versions=versions,
        audits=audits,
        prompts=prompts,
        prompt_config=prompt_config,
        ai_adapter=ai_adapter,
        embedding_adapter=embedding_adapter,
    )
    return service, collaborators


@pytest.mark.asyncio
async def test_valid_ai_output_is_persisted_as_draft() -> None:
    # Arrange
    requirement = SimpleNamespace(
        id=10,
        module_id=3,
        content="User can book from 1 to 8 tickets.",
        acceptance_criteria="Nine tickets must be rejected.",
        created_by=7,
    )
    ai_result = GeneratedBatchResult(
        data=GeneratedTestCaseBatch(
            test_cases=[
                GeneratedTestCase(
                    summary="Check upper boundary",
                    steps=["Select 8 seats", "Confirm booking"],
                    expected_result="The system accepts exactly 8 tickets.",
                    priority=Priority.HIGH,
                    test_techniques=["BVA"],
                )
            ]
        ),
        usage=AIUsage(input_tokens=100, output_tokens=80),
    )
    service, deps = build_service(requirement=requirement, ai_result=ai_result)
    current_user = CurrentUser(id=7, role=UserRole.QA)

    # Act
    result = await service.generate_draft_test_cases(10, current_user)

    # Assert (TE-18: verify schema-checkable facts, never exact free-form model prose)
    assert len(result) == 1
    assert result[0].status == CaseStatus.DRAFT
    assert result[0].requirement_id == 10
    assert result[0].module_id == 3
    assert result[0].priority in {Priority.HIGH, Priority.MEDIUM, Priority.LOW}
    assert len(result[0].steps) >= 1
    deps.prompts.get_active.assert_awaited_once()
    called_prompt = deps.ai_adapter.generate_test_cases.await_args.args[2]
    assert isinstance(called_prompt, PromptRuntimeConfig)
    assert called_prompt.version_number == 2
    deps.test_cases.create_many.assert_awaited_once()
    deps.embedding_adapter.embed_texts.assert_awaited_once()
    deps.test_cases.set_embeddings.assert_awaited_once()
    deps.versions.create_snapshots.assert_awaited_once()
    deps.audits.create.assert_awaited_once()
    deps.session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_qa_cannot_generate_from_another_users_requirement() -> None:
    # Arrange
    requirement = SimpleNamespace(
        id=10,
        module_id=3,
        content="Requirement text long enough for the test.",
        acceptance_criteria=None,
        created_by=99,
    )
    service, deps = build_service(requirement=requirement, ai_result=RuntimeError("must not be called"))
    current_user = CurrentUser(id=7, role=UserRole.QA)

    # Act
    with pytest.raises(AppError) as exc_info:
        await service.generate_draft_test_cases(10, current_user)

    # Assert
    assert exc_info.value.code == ErrorCode.FORBIDDEN_RECORD
    assert exc_info.value.status_code == 403
    deps.ai_adapter.generate_test_cases.assert_not_awaited()
    deps.test_cases.create_many.assert_not_awaited()
    deps.versions.create_snapshots.assert_not_awaited()
    deps.session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_invalid_ai_output_is_not_persisted() -> None:
    # Arrange
    requirement = SimpleNamespace(
        id=10,
        module_id=3,
        content="User can book from 1 to 8 tickets.",
        acceptance_criteria=None,
        created_by=7,
    )
    ai_error = AppError(ErrorCode.AI_OUTPUT_INVALID, "Invalid schema.", 502)
    service, deps = build_service(requirement=requirement, ai_result=ai_error)
    current_user = CurrentUser(id=7, role=UserRole.QA)

    # Act
    with pytest.raises(AppError) as exc_info:
        await service.generate_draft_test_cases(10, current_user)

    # Assert
    assert exc_info.value.code == ErrorCode.AI_OUTPUT_INVALID
    deps.test_cases.create_many.assert_not_awaited()
    deps.versions.create_snapshots.assert_not_awaited()
    deps.audits.create.assert_not_awaited()
    deps.session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_active_prompt_blocks_generation() -> None:
    requirement = SimpleNamespace(
        id=10,
        module_id=3,
        content="Requirement text long enough for the test.",
        acceptance_criteria=None,
        created_by=7,
    )
    service, deps = build_service(requirement=requirement, ai_result=RuntimeError("must not be called"))
    deps.prompts.get_active.return_value = None
    current_user = CurrentUser(id=7, role=UserRole.QA)

    with pytest.raises(AppError) as exc_info:
        await service.generate_draft_test_cases(10, current_user)

    assert exc_info.value.code == ErrorCode.PROMPT_CONFIG_NOT_FOUND
    deps.ai_adapter.generate_test_cases.assert_not_awaited()
    deps.test_cases.create_many.assert_not_awaited()
    deps.session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_requirement_returns_not_found_without_calling_ai() -> None:
    # Arrange
    service, deps = build_service(requirement=None, ai_result=RuntimeError("must not be called"))
    current_user = CurrentUser(id=7, role=UserRole.QA)

    # Act
    with pytest.raises(AppError) as exc_info:
        await service.generate_draft_test_cases(999, current_user)

    # Assert
    assert exc_info.value.code == ErrorCode.REQUIREMENT_NOT_FOUND
    assert exc_info.value.status_code == 404
    deps.ai_adapter.generate_test_cases.assert_not_awaited()
