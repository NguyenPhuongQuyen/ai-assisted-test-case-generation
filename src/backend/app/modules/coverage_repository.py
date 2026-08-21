# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

from dataclasses import dataclass

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import TestCaseStatus
from app.requirements.models import Requirement
from app.testcases.models import TestCase


@dataclass(frozen=True, slots=True)
class ModuleCoverageRecord:
    total_requirements: int
    covered_requirements: int
    total_test_cases: int
    approved_test_cases: int
    status_counts: dict[TestCaseStatus, int]


class ModuleCoverageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_coverage(self, *, module_id: int, owner_id: int | None) -> ModuleCoverageRecord:
        total_requirements = await self._count_requirements(module_id=module_id, owner_id=owner_id)
        covered_requirements = await self._count_covered_requirements(module_id=module_id, owner_id=owner_id)
        status_counts = await self._count_test_cases_by_status(module_id=module_id, owner_id=owner_id)
        total_test_cases = sum(status_counts.values())
        approved_test_cases = status_counts[TestCaseStatus.APPROVED]
        return ModuleCoverageRecord(
            total_requirements=total_requirements,
            covered_requirements=covered_requirements,
            total_test_cases=total_test_cases,
            approved_test_cases=approved_test_cases,
            status_counts=status_counts,
        )

    async def _count_requirements(self, *, module_id: int, owner_id: int | None) -> int:
        statement = select(func.count()).select_from(Requirement).where(Requirement.module_id == module_id)
        if owner_id is not None:
            statement = statement.where(Requirement.created_by == owner_id)
        result = await self._session.execute(statement)
        return int(result.scalar_one())

    async def _count_covered_requirements(self, *, module_id: int, owner_id: int | None) -> int:
        case_conditions = [
            TestCase.requirement_id == Requirement.id,
            TestCase.status != TestCaseStatus.REJECTED,
        ]
        if owner_id is not None:
            case_conditions.append(TestCase.created_by == owner_id)
        covered_case = select(TestCase.id).where(*case_conditions).exists()
        statement = (
            select(func.count()).select_from(Requirement).where(Requirement.module_id == module_id, covered_case)
        )
        if owner_id is not None:
            statement = statement.where(Requirement.created_by == owner_id)
        result = await self._session.execute(statement)
        return int(result.scalar_one())

    async def _count_test_cases_by_status(
        self,
        *,
        module_id: int,
        owner_id: int | None,
    ) -> dict[TestCaseStatus, int]:
        columns = [
            func.sum(case((TestCase.status == status, 1), else_=0)).label(status.value) for status in TestCaseStatus
        ]
        statement = select(*columns).select_from(TestCase).where(TestCase.module_id == module_id)
        if owner_id is not None:
            statement = statement.where(TestCase.created_by == owner_id)
        result = (await self._session.execute(statement)).one()
        return {status: int(getattr(result, status.value) or 0) for status in TestCaseStatus}
