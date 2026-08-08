from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import AuthResponse, LoginRequest
from app.common.constants import ErrorCode
from app.common.exceptions import AppError
from app.common.security import create_access_token, verify_password
from app.users.repository import UserRepository
from app.users.schemas import UserResponse

MAX_FAILED_LOGIN_ATTEMPTS = 5
ACCOUNT_LOCK_MINUTES = 15


class AuthService:
    def __init__(self, session: AsyncSession, users: UserRepository) -> None:
        self._session = session
        self._users = users

    async def login(self, payload: LoginRequest) -> AuthResponse:
        """Authenticate a user, lock repeated failures temporarily, and issue a short-lived JWT."""
        user = await self._users.get_by_email(str(payload.email))
        if user is None:
            raise AppError(ErrorCode.INVALID_CREDENTIALS, "Email hoặc mật khẩu không đúng.", 401)

        now = datetime.now(UTC)
        if user.locked_until is not None and user.locked_until > now:
            raise AppError(ErrorCode.ACCOUNT_LOCKED, "Tài khoản đang tạm khóa do đăng nhập sai nhiều lần.", 429)

        if not verify_password(payload.password, user.password_hash):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
                user.locked_until = now + timedelta(minutes=ACCOUNT_LOCK_MINUTES)
            await self._session.commit()
            raise AppError(ErrorCode.INVALID_CREDENTIALS, "Email hoặc mật khẩu không đúng.", 401)

        user.failed_login_attempts = 0
        user.locked_until = None
        await self._session.commit()
        token = create_access_token(user.id, user.role)
        return AuthResponse(
            access_token=token,
            user=UserResponse(id=user.id, email=user.email, role=user.role),
        )
