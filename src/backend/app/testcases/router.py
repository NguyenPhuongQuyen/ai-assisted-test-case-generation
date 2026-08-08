from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.repository import AuditLogRepository
from app.auth.dependencies import get_current_user
from app.auth.schemas import CurrentUser
from app.common.ai.openai_adapter import OpenAIAdapter
from app.common.config import get_settings
from app.common.database import get_session
from app.common.rate_limit import SlidingWindowRateLimiter
from app.requirements.repository import RequirementRepository
from app.testcases.repository import TestCaseRepository
from app.testcases.schemas import GenerationResponse, TestCaseResponse
from app.testcases.service import TestCaseGenerationService

router = APIRouter(tags=["test-cases"])
settings = get_settings()
ai_rate_limiter = SlidingWindowRateLimiter(
    max_requests=settings.ai_rate_limit_max_requests,
    window_seconds=settings.ai_rate_limit_window_seconds,
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


def build_service(session: AsyncSession) -> TestCaseGenerationService:
    return TestCaseGenerationService(
        session=session,
        requirements=RequirementRepository(session),
        test_cases=TestCaseRepository(session),
        audits=AuditLogRepository(session),
        ai_adapter=OpenAIAdapter(),
        rate_limiter=ai_rate_limiter,
    )


@router.post(
    "/requirements/{requirement_id}/test-cases",
    response_model=GenerationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_test_cases(
    requirement_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> GenerationResponse:
    records = await build_service(session).generate_draft_test_cases(requirement_id, current_user)
    return GenerationResponse(
        requirement_id=requirement_id,
        test_cases=[
            TestCaseResponse(
                id=item.id,
                requirement_id=item.requirement_id,
                module_id=item.module_id,
                summary=item.summary,
                preconditions=item.preconditions,
                steps=item.steps,
                expected_result=item.expected_result,
                priority=item.priority,
                test_techniques=item.test_techniques,
                review_note=item.review_note,
                status=item.status,
            )
            for item in records
        ],
    )
