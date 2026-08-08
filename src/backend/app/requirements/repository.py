from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.requirements.models import Requirement


class RequirementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, requirement: Requirement) -> Requirement:
        self._session.add(requirement)
        await self._session.flush()
        return requirement

    async def get_by_id(self, requirement_id: int) -> Requirement | None:
        result = await self._session.execute(select(Requirement).where(Requirement.id == requirement_id))
        return result.scalar_one_or_none()
