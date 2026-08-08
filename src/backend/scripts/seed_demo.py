import asyncio

from app.common.config import get_settings
from app.common.constants import UserRole
from app.common.database import SessionFactory
from app.common.security import hash_password
from app.modules.models import Module
from app.users.models import User
from sqlalchemy import select


async def _get_or_create_user(email: str, role: UserRole, password_hash: str) -> User:
    async with SessionFactory() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(email=email, password_hash=password_hash, role=role)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


async def seed() -> None:
    """Create fake demo accounts and one module; passwords are bcrypt-hashed before persistence."""
    settings = get_settings()
    password_hash = hash_password(settings.demo_user_password)
    admin = await _get_or_create_user("admin@example.com", UserRole.ADMIN, password_hash)
    await _get_or_create_user("manager@example.com", UserRole.MANAGER, password_hash)
    await _get_or_create_user("qa@example.com", UserRole.QA, password_hash)

    async with SessionFactory() as session:
        result = await session.execute(select(Module).where(Module.name == "Booking"))
        if result.scalar_one_or_none() is None:
            session.add(Module(name="Booking", created_by=admin.id))
            await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
