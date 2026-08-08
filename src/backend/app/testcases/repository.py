from sqlalchemy.ext.asyncio import AsyncSession

from app.testcases.models import TestCase


class TestCaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_many(self, test_cases: list[TestCase]) -> list[TestCase]:
        self._session.add_all(test_cases)
        await self._session.flush()
        return test_cases
