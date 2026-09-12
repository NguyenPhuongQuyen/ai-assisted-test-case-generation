from sqlalchemy import func, select
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

    async def get_by_id_for_update(self, requirement_id: int) -> Requirement | None:
        statement = select(Requirement).where(Requirement.id == requirement_id).with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_by_module_and_creator(
        self,
        module_id: int,
        created_by: int,
        page: int,
        page_size: int,
    ) -> tuple[list[Requirement], int]:
        filters = (
            Requirement.module_id == module_id,
            Requirement.created_by == created_by,
        )
        statement = (
            select(Requirement)
            .where(*filters)
            .order_by(Requirement.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self._session.execute(statement)

        total_result = await self._session.execute(select(func.count()).select_from(Requirement).where(*filters))
        return list(result.scalars().all()), int(total_result.scalar_one())

    async def save(self, requirement: Requirement) -> Requirement:
        self._session.add(requirement)
        await self._session.flush()
        return requirement
