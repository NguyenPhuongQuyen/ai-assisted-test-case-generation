# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.testcases.version_models import TestCaseVersion


class TestCaseVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_snapshot(self, *, test_case_id: int, snapshot: dict, created_by: int) -> TestCaseVersion:
        statement = select(func.coalesce(func.max(TestCaseVersion.version_number), 0)).where(
            TestCaseVersion.test_case_id == test_case_id
        )
        result = await self._session.execute(statement)
        version_number = int(result.scalar_one()) + 1
        version = TestCaseVersion(
            test_case_id=test_case_id,
            version_number=version_number,
            snapshot=snapshot,
            created_by=created_by,
        )
        self._session.add(version)
        await self._session.flush()
        return version
