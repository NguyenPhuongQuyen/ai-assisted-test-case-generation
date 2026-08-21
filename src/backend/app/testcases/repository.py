# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import TestCaseStatus
from app.testcases.models import TestCase


class TestCaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_many(self, test_cases: list[TestCase]) -> list[TestCase]:
        self._session.add_all(test_cases)
        await self._session.flush()
        return test_cases

    async def get_by_id(self, test_case_id: int) -> TestCase | None:
        result = await self._session.execute(select(TestCase).where(TestCase.id == test_case_id))
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, test_case_id: int) -> TestCase | None:
        statement = select(TestCase).where(TestCase.id == test_case_id).with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def save(self, test_case: TestCase) -> TestCase:
        self._session.add(test_case)
        await self._session.flush()
        return test_case

    async def list_accessible(
        self,
        *,
        owner_id: int | None,
        requirement_id: int | None,
        case_status: TestCaseStatus | None,
        offset: int,
        limit: int,
    ) -> list[TestCase]:
        statement = self._apply_filters(
            select(TestCase),
            owner_id=owner_id,
            requirement_id=requirement_id,
            case_status=case_status,
        )
        result = await self._session.execute(statement.order_by(TestCase.id.desc()).offset(offset).limit(limit))
        return list(result.scalars().all())

    async def count_accessible(
        self,
        *,
        owner_id: int | None,
        requirement_id: int | None,
        case_status: TestCaseStatus | None,
    ) -> int:
        statement = self._apply_filters(
            select(func.count()).select_from(TestCase),
            owner_id=owner_id,
            requirement_id=requirement_id,
            case_status=case_status,
        )
        result = await self._session.execute(statement)
        return int(result.scalar_one())

    @staticmethod
    def _apply_filters(
        statement,
        *,
        owner_id: int | None,
        requirement_id: int | None,
        case_status: TestCaseStatus | None,
    ):
        if owner_id is not None:
            statement = statement.where(TestCase.created_by == owner_id)
        if requirement_id is not None:
            statement = statement.where(TestCase.requirement_id == requirement_id)
        if case_status is not None:
            statement = statement.where(TestCase.status == case_status)
        return statement
