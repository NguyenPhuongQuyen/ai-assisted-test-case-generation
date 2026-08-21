import asyncio
import logging

from celery import shared_task

from app.audit.repository import AuditLogRepository
from app.auth.schemas import CurrentUser
from app.common.ai.openai_adapter import OpenAIAdapter
from app.common.constants import (
    GENERATION_TASK_NAME,
    ErrorCode,
    GenerationJobStatus,
)
from app.common.database import get_session_factory
from app.common.exceptions import AppError
from app.requirements.repository import RequirementRepository
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

        await jobs.set_status(
            job,
            GenerationJobStatus.FAILED,
            error_code,
        )
        await session.commit()


async def _run_generation_job(job_id: int) -> None:
    session_factory = get_session_factory()

    async with session_factory() as session:
        jobs = GenerationJobRepository(session)
        job = await jobs.get_by_id(job_id)

        if job is None:
            logger.error(
                "Generation job not found",
                extra={"generation_job_id": job_id},
            )
            return

        await jobs.set_status(
            job,
            GenerationJobStatus.RUNNING,
        )
        await session.commit()

        user = await UserRepository(session).get_by_id(job.created_by)

        if user is None:
            await _mark_failed(
                job_id,
                ErrorCode.UNAUTHORIZED.value,
            )
            return

        service = TestCaseGenerationService(
            session=session,
            requirements=RequirementRepository(session),
            test_cases=TestCaseRepository(session),
            versions=TestCaseVersionRepository(session),
            audits=AuditLogRepository(session),
            ai_adapter=OpenAIAdapter(),
        )

        try:
            await service.generate_draft_test_cases(
                job.requirement_id,
                CurrentUser(
                    id=user.id,
                    role=user.role,
                ),
            )

        except AppError as exc:
            logger.exception(
                "Generation job failed with application error",
                extra={
                    "generation_job_id": job.id,
                    "requirement_id": job.requirement_id,
                    "user_id": job.created_by,
                    "error_code": exc.code.value,
                },
            )
            await _mark_failed(
                job_id,
                exc.code.value,
            )
            return

        except Exception:
            logger.exception(
                "Generation job failed unexpectedly",
                extra={
                    "generation_job_id": job.id,
                    "requirement_id": job.requirement_id,
                    "user_id": job.created_by,
                },
            )
            await _mark_failed(
                job_id,
                ErrorCode.INTERNAL_SERVER_ERROR.value,
            )
            return

        await jobs.set_status(
            job,
            GenerationJobStatus.COMPLETED,
        )
        await session.commit()


@shared_task(name=GENERATION_TASK_NAME)
def generate_test_cases_task(job_id: int) -> None:
    asyncio.run(_run_generation_job(job_id))
