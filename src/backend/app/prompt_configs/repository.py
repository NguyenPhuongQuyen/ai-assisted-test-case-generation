# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.prompt_configs.models import PromptConfig


class PromptConfigRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active(self) -> PromptConfig | None:
        statement = select(PromptConfig).where(PromptConfig.is_active.is_(True)).limit(1)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def deactivate_active(self) -> None:
        statement = update(PromptConfig).where(PromptConfig.is_active.is_(True)).values(is_active=False)
        await self._session.execute(statement)

    async def next_version_number(self) -> int:
        result = await self._session.execute(select(func.max(PromptConfig.version_number)))
        current = result.scalar_one_or_none()
        return int(current or 0) + 1

    async def create(self, config: PromptConfig) -> PromptConfig:
        self._session.add(config)
        await self._session.flush()
        return config

    async def list_all(self, *, offset: int, limit: int) -> list[PromptConfig]:
        statement = select(PromptConfig).order_by(PromptConfig.version_number.desc()).offset(offset).limit(limit)
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def count_all(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(PromptConfig))
        return int(result.scalar_one())
