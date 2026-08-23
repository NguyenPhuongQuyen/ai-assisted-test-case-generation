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

    async def list_for_test_case(self, test_case_id: int, *, offset: int, limit: int) -> list[TestCaseVersion]:
        statement = (
            select(TestCaseVersion)
            .where(TestCaseVersion.test_case_id == test_case_id)
            .order_by(TestCaseVersion.version_number.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def count_for_test_case(self, test_case_id: int) -> int:
        statement = (
            select(func.count()).select_from(TestCaseVersion).where(TestCaseVersion.test_case_id == test_case_id)
        )
        result = await self._session.execute(statement)
        return int(result.scalar_one())

    async def get_by_number(self, test_case_id: int, version_number: int) -> TestCaseVersion | None:
        statement = select(TestCaseVersion).where(
            TestCaseVersion.test_case_id == test_case_id,
            TestCaseVersion.version_number == version_number,
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()
