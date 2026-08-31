from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.models import Module


class ModuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, module_id: int) -> Module | None:
        result = await self._session.execute(select(Module).where(Module.id == module_id))
        return result.scalar_one_or_none()

    async def get_parent_chain(self, parent_id: int) -> tuple[list[int], bool]:
        statement = text(
            """
            WITH RECURSIVE parent_chain AS (
                SELECT
                    id,
                    parent_id,
                    ARRAY[id] AS path,
                    FALSE AS has_cycle
                FROM modules
                WHERE id = :parent_id

                UNION ALL

                SELECT
                    parent.id,
                    parent.parent_id,
                    child.path || parent.id,
                    parent.id = ANY(child.path)
                FROM modules AS parent
                JOIN parent_chain AS child
                    ON parent.id = child.parent_id
                WHERE NOT child.has_cycle
            )
            SELECT id, has_cycle
            FROM parent_chain
            """
        )
        result = await self._session.execute(
            statement,
            {"parent_id": parent_id},
        )
        rows = result.mappings().all()

        ids = [int(row["id"]) for row in rows]
        has_cycle = any(bool(row["has_cycle"]) for row in rows)
        return ids, has_cycle

    async def create(self, module: Module) -> Module:
        self._session.add(module)
        await self._session.flush()
        return module

    async def save(self, module: Module) -> Module:
        self._session.add(module)
        await self._session.flush()
        return module

    async def list_all(self, *, offset: int, limit: int) -> list[Module]:
        statement = select(Module).order_by(Module.name.asc(), Module.id.asc()).offset(offset).limit(limit)
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def count_all(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(Module))
        return int(result.scalar_one())

    async def exists_with_name(
        self,
        *,
        name: str,
        parent_id: int | None,
        exclude_id: int | None,
    ) -> bool:
        statement = select(Module.id).where(func.lower(Module.name) == name.lower())
        if parent_id is None:
            statement = statement.where(Module.parent_id.is_(None))
        else:
            statement = statement.where(Module.parent_id == parent_id)
        if exclude_id is not None:
            statement = statement.where(Module.id != exclude_id)
        result = await self._session.execute(statement.limit(1))
        return result.scalar_one_or_none() is not None
