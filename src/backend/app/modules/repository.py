from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.models import Module


class ModuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, module_id: int) -> Module | None:
        result = await self._session.execute(select(Module).where(Module.id == module_id))
        return result.scalar_one_or_none()
