from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import CurrentUser
from app.common.constants import ErrorCode, UserRole
from app.common.exceptions import AppError
from app.common.security import hash_password
from app.users.models import User
from app.users.repository import UserRepository
from app.users.schemas import UserCreateRequest, UserResponse


class UserService:
    def __init__(self, session: AsyncSession, users: UserRepository) -> None:
        self._session = session
        self._users = users

    async def create_user(self, payload: UserCreateRequest, current_user: CurrentUser) -> UserResponse:
        """Create a user account only when requested by an authenticated Admin (SE-05, UC02)."""
        if current_user.role != UserRole.ADMIN:
            raise AppError(ErrorCode.FORBIDDEN_ROLE, "Chỉ Admin được quản lý tài khoản người dùng.", 403)

        if await self._users.get_by_email(str(payload.email)) is not None:
            raise AppError(ErrorCode.USER_ALREADY_EXISTS, "Email đã được sử dụng.", 409)

        # SE-02: only the bcrypt hash is persisted; plaintext password never enters the database.
        user = User(
            email=str(payload.email),
            password_hash=hash_password(payload.password),
            role=payload.role,
        )
        await self._users.create(user)
        await self._session.commit()
        return UserResponse(id=user.id, email=user.email, role=user.role)
