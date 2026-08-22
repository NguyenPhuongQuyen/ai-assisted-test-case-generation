# Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).

import asyncio
import logging

from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.repository import AuditLogRepository
from app.auth.schemas import CurrentUser
from app.common.ai.embedding_adapter import OpenAIEmbeddingAdapter
from app.common.ai.openai_adapter import OpenAIAdapter
from app.common.constants import GENERATION_TASK_NAME, ErrorCode, GenerationJobStatus
from app.common.database import get_session_factory
from app.common.exceptions import AppError
from app.prompt_configs.repository import PromptConfigRepository
from app.requirements.repository import RequirementRepository
from app.testcases.job_models import GenerationJob
from app.testcases.job_repository import GenerationJobRepository
from app.testcases.repository import TestCaseRepository
from app.testcases.service import TestCaseGenerationService
from app.testcases.version_repository import TestCaseVersionRepository
from app.users.repository import UserRepository

logger = logging.getLogger(__name__)


async def _mark_failed(job_id: int, error_code: str) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        jobs = GenerationJobRepository(session)
        job = await jobs.get_by_id(job_id)
        if job is None:
            return
        await jobs.set_status(job, GenerationJobStatus.FAILED, error_code)
        await session.commit()


def _build_generation_service(session: AsyncSession) -> TestCaseGenerationService:
    return TestCaseGenerationService(
        session=session,
        requirements=RequirementRepository(session),
        test_cases=TestCaseRepository(session),
        versions=TestCaseVersionRepository(session),
        audits=AuditLogRepository(session),
        prompts=PromptConfigRepository(session),
        ai_adapter=OpenAIAdapter(),
        embedding_adapter=OpenAIEmbeddingAdapter(),
    )


async def _load_job_and_user(session: AsyncSession, job_id: int) -> tuple[GenerationJob | None, CurrentUser | None]:
    jobs = GenerationJobRepository(session)
    job = await jobs.get_by_id(job_id)
    if job is None:
        logger.error("Generation job not found", extra={"generation_job_id": job_id})
        return None, None
    await jobs.set_status(job, GenerationJobStatus.RUNNING)
    await session.commit()
    user = await UserRepository(session).get_by_id(job.created_by)
    current_user = CurrentUser(id=user.id, role=user.role) if user is not None else None
    return job, current_user


async def _execute_generation(session: AsyncSession, job: GenerationJob, current_user: CurrentUser) -> str | None:
    try:
        await _build_generation_service(session).generate_draft_test_cases(job.requirement_id, current_user)
    except AppError as exc:
        logger.exception(
            "Generation job failed with application error",
            extra={"generation_job_id": job.id, "requirement_id": job.requirement_id, "error_code": exc.code.value},
        )
        return exc.code.value
    except Exception:
        logger.exception(
            "Generation job failed unexpectedly",
            extra={"generation_job_id": job.id, "requirement_id": job.requirement_id},
        )
        return ErrorCode.INTERNAL_SERVER_ERROR.value
    return None


async def _run_generation_job(job_id: int) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        job, current_user = await _load_job_and_user(session, job_id)
        if job is None:
            return
        if current_user is None:
            await _mark_failed(job_id, ErrorCode.UNAUTHORIZED.value)
            return
        error_code = await _execute_generation(session, job, current_user)
        if error_code is not None:
            await _mark_failed(job_id, error_code)
            return
        await GenerationJobRepository(session).set_status(job, GenerationJobStatus.COMPLETED)
        await session.commit()


@shared_task(name=GENERATION_TASK_NAME)
def generate_test_cases_task(job_id: int) -> None:
    asyncio.run(_run_generation_job(job_id))
