# Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        """Return one user by normalized email."""
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        """Return one user by primary key."""
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def list_page(self, page: int, page_size: int) -> tuple[list[User], int]:
        """Return one database-paginated page and total count (AP-04)."""
        offset = (page - 1) * page_size
        rows = await self._session.execute(select(User).order_by(User.id).offset(offset).limit(page_size))
        total_result = await self._session.execute(select(func.count(User.id)))
        return list(rows.scalars().all()), int(total_result.scalar_one())

    async def create(self, user: User) -> User:
        """Persist a new user without committing the surrounding transaction."""
        self._session.add(user)
        await self._session.flush()
        return user
