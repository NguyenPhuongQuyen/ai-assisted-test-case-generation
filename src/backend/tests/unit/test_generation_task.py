from unittest.mock import AsyncMock, MagicMock

import pytest
from app.common.constants import ErrorCode, UserRole
from app.common.exceptions import AppError
from app.testcases import tasks


@pytest.mark.asyncio
async def test_generation_job_preserves_app_error_code(monkeypatch):
    job = MagicMock()
    job.id = 1
    job.requirement_id = 5
    job.created_by = 3

    jobs = MagicMock()
    jobs.get_by_id = AsyncMock(return_value=job)
    jobs.set_status = AsyncMock()

    user = MagicMock()
    user.id = 3
    user.role = UserRole.QA

    users = MagicMock()
    users.get_by_id = AsyncMock(return_value=user)

    session = MagicMock()
    session.commit = AsyncMock()

    session_context = AsyncMock()
    session_context.__aenter__.return_value = session

    session_factory = MagicMock(return_value=session_context)

    service = MagicMock()
    service.generate_draft_test_cases = AsyncMock(
        side_effect=AppError(
            code=ErrorCode.AI_PROVIDER_ERROR,
            message="AI provider failed",
            status_code=502,
        )
    )

    mark_failed = AsyncMock()

    monkeypatch.setattr(tasks, "get_session_factory", lambda: session_factory)
    monkeypatch.setattr(tasks, "GenerationJobRepository", lambda _: jobs)
    monkeypatch.setattr(tasks, "UserRepository", lambda _: users)
    monkeypatch.setattr(tasks, "TestCaseGenerationService", lambda **_: service)
    monkeypatch.setattr(tasks, "_mark_failed", mark_failed)

    await tasks._run_generation_job(1)

    mark_failed.assert_awaited_once_with(
        1,
        ErrorCode.AI_PROVIDER_ERROR.value,
    )
