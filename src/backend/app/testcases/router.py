from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.schemas import CurrentUser
from app.common.config import get_settings
from app.common.database import get_session
from app.common.rate_limit import SlidingWindowRateLimiter
from app.common.task_queue import GenerationTaskQueue
from app.requirements.repository import RequirementRepository
from app.testcases.job_repository import GenerationJobRepository
from app.testcases.job_service import GenerationJobService
from app.testcases.schemas import GenerationJobResponse

router = APIRouter(tags=["test-cases"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


@lru_cache
def get_ai_rate_limiter() -> SlidingWindowRateLimiter:
    settings = get_settings()
    return SlidingWindowRateLimiter(
        max_requests=settings.ai_rate_limit_max_requests,
        window_seconds=settings.ai_rate_limit_window_seconds,
    )


def build_job_service(session: AsyncSession) -> GenerationJobService:
    return GenerationJobService(
        session=session,
        requirements=RequirementRepository(session),
        jobs=GenerationJobRepository(session),
        task_queue=GenerationTaskQueue(),
        rate_limiter=get_ai_rate_limiter(),
    )


def to_job_response(job) -> GenerationJobResponse:
    return GenerationJobResponse(
        id=job.id,
        requirement_id=job.requirement_id,
        status=job.status,
        error_code=job.error_code,
    )


@router.post(
    "/requirements/{requirement_id}/test-cases",
    response_model=GenerationJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_test_cases(
    requirement_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> GenerationJobResponse:
    job = await build_job_service(session).submit(requirement_id, current_user)
    return to_job_response(job)


@router.get(
    "/generation-jobs/{job_id}",
    response_model=GenerationJobResponse,
)
async def get_generation_job(
    job_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> GenerationJobResponse:
    job = await build_job_service(session).get_status(job_id, current_user)
    return to_job_response(job)
