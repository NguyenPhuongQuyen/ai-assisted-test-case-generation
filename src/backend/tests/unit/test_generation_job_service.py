from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from app.auth.schemas import CurrentUser
from app.common.constants import ErrorCode, GenerationJobStatus, UserRole
from app.common.exceptions import AppError
from app.testcases.job_service import GenerationJobService


def build_service(*, requirement=None, job=None):
    session = AsyncMock()
    requirements = SimpleNamespace(get_by_id=AsyncMock(return_value=requirement))
    jobs = SimpleNamespace(
        create=AsyncMock(),
        get_by_id=AsyncMock(return_value=job),
        set_status=AsyncMock(),
    )
    task_queue = SimpleNamespace(enqueue=Mock())
    rate_limiter = SimpleNamespace(check=AsyncMock())

    async def create_job(record):
        record.id = 42
        return record

    jobs.create.side_effect = create_job

    service = GenerationJobService(
        session=session,
        requirements=requirements,
        jobs=jobs,
        task_queue=task_queue,
        rate_limiter=rate_limiter,
    )
    deps = SimpleNamespace(
        session=session,
        requirements=requirements,
        jobs=jobs,
        task_queue=task_queue,
        rate_limiter=rate_limiter,
    )
    return service, deps


@pytest.mark.asyncio
async def test_submit_generation_creates_queued_job_and_enqueues() -> None:
    requirement = SimpleNamespace(id=10, created_by=7)
    service, deps = build_service(requirement=requirement)
    user = CurrentUser(id=7, role=UserRole.QA)

    job = await service.submit(10, user)

    assert job.id == 42
    assert job.requirement_id == 10
    assert job.created_by == 7
    assert job.status == GenerationJobStatus.QUEUED
    deps.rate_limiter.check.assert_awaited_once_with("ai-generation:7")
    deps.jobs.create.assert_awaited_once()
    deps.session.commit.assert_awaited_once()
    deps.task_queue.enqueue.assert_called_once_with(42)


@pytest.mark.asyncio
async def test_submit_other_users_requirement_is_forbidden() -> None:
    requirement = SimpleNamespace(id=10, created_by=99)
    service, deps = build_service(requirement=requirement)
    user = CurrentUser(id=7, role=UserRole.QA)

    with pytest.raises(AppError) as exc_info:
        await service.submit(10, user)

    assert exc_info.value.code == ErrorCode.FORBIDDEN_RECORD
    assert exc_info.value.status_code == 403
    deps.jobs.create.assert_not_awaited()
    deps.task_queue.enqueue.assert_not_called()


@pytest.mark.asyncio
async def test_get_other_users_job_is_forbidden() -> None:
    job = SimpleNamespace(id=42, requirement_id=10, created_by=99)
    service, _ = build_service(job=job)
    user = CurrentUser(id=7, role=UserRole.QA)

    with pytest.raises(AppError) as exc_info:
        await service.get_status(42, user)

    assert exc_info.value.code == ErrorCode.FORBIDDEN_RECORD
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_queue_failure_marks_job_failed() -> None:
    requirement = SimpleNamespace(id=10, created_by=7)
    service, deps = build_service(requirement=requirement)
    user = CurrentUser(id=7, role=UserRole.QA)
    deps.task_queue.enqueue.side_effect = RuntimeError("broker unavailable")

    with pytest.raises(AppError) as exc_info:
        await service.submit(10, user)

    assert exc_info.value.code == ErrorCode.GENERATION_QUEUE_UNAVAILABLE
    deps.jobs.set_status.assert_awaited_once()
    args = deps.jobs.set_status.await_args.args
    assert args[1] == GenerationJobStatus.FAILED
