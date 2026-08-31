from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import GenerationJobStatus
from app.testcases.job_models import GenerationJob


class GenerationJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, job_id: int) -> GenerationJob | None:
        result = await self._session.execute(select(GenerationJob).where(GenerationJob.id == job_id))
        return result.scalar_one_or_none()

    async def create(self, job: GenerationJob) -> GenerationJob:
        self._session.add(job)
        await self._session.flush()
        return job

    async def set_status(
        self,
        job: GenerationJob,
        status: GenerationJobStatus,
        error_code: str | None = None,
    ) -> GenerationJob:
        job.status = status
        job.error_code = error_code
        await self._session.flush()
        return job
