# Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import CurrentUser
from app.common.constants import ErrorCode, GenerationJobStatus, UserRole
from app.common.exceptions import AppError
from app.common.rate_limit import SlidingWindowRateLimiter
from app.common.task_queue import GenerationTaskQueue
from app.requirements.repository import RequirementRepository
from app.testcases.job_models import GenerationJob
from app.testcases.job_repository import GenerationJobRepository

logger = logging.getLogger(__name__)


class GenerationJobService:
    def __init__(
        self,
        session: AsyncSession,
        requirements: RequirementRepository,
        jobs: GenerationJobRepository,
        task_queue: GenerationTaskQueue,
        rate_limiter: SlidingWindowRateLimiter,
    ) -> None:
        self._session = session
        self._requirements = requirements
        self._jobs = jobs
        self._task_queue = task_queue
        self._rate_limiter = rate_limiter

    async def submit(
        self,
        requirement_id: int,
        current_user: CurrentUser,
    ) -> GenerationJob:
        """Validate a generation request, persist a queued job and enqueue it."""
        requirement = await self._require_accessible_requirement(requirement_id, current_user)
        await self._rate_limiter.check(f"ai-generation:{current_user.id}")
        job = GenerationJob(
            requirement_id=requirement.id,
            created_by=current_user.id,
            status=GenerationJobStatus.QUEUED,
        )
        await self._jobs.create(job)
        await self._session.commit()
        await self._enqueue_or_fail(job, requirement.id, current_user.id)
        return job

    async def _require_accessible_requirement(
        self,
        requirement_id: int,
        current_user: CurrentUser,
    ):  # type: ignore[no-untyped-def]
        requirement = await self._requirements.get_by_id(requirement_id)
        if requirement is None:
            raise AppError(ErrorCode.REQUIREMENT_NOT_FOUND, "Không tìm thấy yêu cầu.", 404)
        allowed_roles = {UserRole.MANAGER, UserRole.ADMIN}
        if requirement.created_by != current_user.id and current_user.role not in allowed_roles:
            raise AppError(ErrorCode.FORBIDDEN_RECORD, "Bạn không có quyền truy cập yêu cầu này.", 403)
        return requirement

    async def _enqueue_or_fail(self, job: GenerationJob, requirement_id: int, user_id: int) -> None:
        try:
            self._task_queue.enqueue(job.id)
        except Exception as exc:
            await self._jobs.set_status(job, GenerationJobStatus.FAILED, ErrorCode.GENERATION_QUEUE_UNAVAILABLE.value)
            await self._session.commit()
            logger.exception(
                "Failed to enqueue generation job",
                extra={"generation_job_id": job.id, "requirement_id": requirement_id, "user_id": user_id},
            )
            raise AppError(
                ErrorCode.GENERATION_QUEUE_UNAVAILABLE,
                "Không thể đưa yêu cầu sinh test case vào hàng đợi.",
                500,
            ) from exc

    async def get_status(
        self,
        job_id: int,
        current_user: CurrentUser,
    ) -> GenerationJob:
        """Return one generation job after record-level authorization."""
        job = await self._jobs.get_by_id(job_id)
        if job is None:
            raise AppError(
                ErrorCode.GENERATION_JOB_NOT_FOUND,
                "Không tìm thấy tác vụ sinh test case.",
                404,
            )

        if job.created_by != current_user.id and current_user.role not in {UserRole.MANAGER, UserRole.ADMIN}:
            raise AppError(
                ErrorCode.FORBIDDEN_RECORD,
                "Bạn không có quyền truy cập tác vụ này.",
                403,
            )

        return job
