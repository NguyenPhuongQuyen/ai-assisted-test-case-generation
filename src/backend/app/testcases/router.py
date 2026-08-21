from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.schemas import CurrentUser
from app.common.config import get_settings
from app.common.constants import TestCaseStatus
from app.common.database import get_session
from app.common.rate_limit import SlidingWindowRateLimiter
from app.common.task_queue import GenerationTaskQueue
from app.requirements.repository import RequirementRepository
from app.testcases.job_repository import GenerationJobRepository
from app.testcases.job_service import GenerationJobService
from app.testcases.query_service import TestCaseQueryService
from app.testcases.repository import TestCaseRepository
from app.testcases.schemas import GenerationJobResponse, TestCaseListResponse, TestCaseResponse

router = APIRouter(tags=["test-cases"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
RequirementFilter = Annotated[int | None, Query(ge=1)]
StatusFilter = Annotated[TestCaseStatus | None, Query(alias="status")]
PageParam = Annotated[int, Query(ge=1)]
PageSizeParam = Annotated[int, Query(alias="pageSize", ge=1, le=100)]
TestCaseIdParam = Annotated[int, Path(ge=1)]


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


def build_query_service(session: AsyncSession) -> TestCaseQueryService:
    return TestCaseQueryService(TestCaseRepository(session))


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


@router.get("/test-cases", response_model=TestCaseListResponse)
async def list_test_cases(
    session: SessionDep,
    current_user: CurrentUserDep,
    requirement_id: RequirementFilter = None,
    case_status: StatusFilter = None,
    page: PageParam = 1,
    page_size: PageSizeParam = 20,
) -> TestCaseListResponse:
    offset = (page - 1) * page_size
    items, total = await build_query_service(session).list_test_cases(
        current_user,
        requirement_id=requirement_id,
        case_status=case_status,
        offset=offset,
        limit=page_size,
    )
    return TestCaseListResponse(data=items, total=total, page=page, page_size=page_size)


@router.get("/test-cases/{test_case_id}", response_model=TestCaseResponse)
async def get_test_case(
    test_case_id: TestCaseIdParam,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> TestCaseResponse:
    test_case = await build_query_service(session).get_test_case(test_case_id, current_user)
    return TestCaseResponse.model_validate(test_case)
