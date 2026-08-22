# Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.audit.repository import AuditLogRepository
from app.common.auth_context import CurrentUser
from app.common.constants import AuditAction, ErrorCode, UserRole
from app.common.exceptions import AppError
from app.common.security import hash_password
from app.users.models import User
from app.users.repository import UserRepository
from app.users.schemas import (
    UserCreateRequest,
    UserListResponse,
    UserResponse,
    UserUpdateRequest,
)


def _snapshot(user: User) -> dict[str, object]:
    return {"id": user.id, "email": user.email, "role": user.role.value, "isActive": user.is_active}


class UserService:
    def __init__(self, session: AsyncSession, users: UserRepository, audits: AuditLogRepository) -> None:
        self._session = session
        self._users = users
        self._audits = audits

    def _require_admin(self, current_user: CurrentUser) -> None:
        if current_user.role != UserRole.ADMIN:
            raise AppError(ErrorCode.FORBIDDEN_ROLE, "Chỉ Admin được quản lý tài khoản người dùng.", 403)

    async def list_users(self, page: int, page_size: int, current_user: CurrentUser) -> UserListResponse:
        """List users for Admin with database pagination (NC-10, AP-04)."""
        self._require_admin(current_user)
        users, total = await self._users.list_page(page, page_size)
        return UserListResponse(
            data=[UserResponse.model_validate(user) for user in users],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def create_user(self, payload: UserCreateRequest, current_user: CurrentUser) -> UserResponse:
        """Create a user and append an audit record when requested by Admin (NC-10, BR-07)."""
        self._require_admin(current_user)
        if await self._users.get_by_email(str(payload.email)) is not None:
            raise AppError(ErrorCode.USER_ALREADY_EXISTS, "Email đã được sử dụng.", 409)
        user = User(
            email=str(payload.email),
            password_hash=hash_password(payload.password),
            role=payload.role,
            is_active=True,
        )
        await self._users.create(user)
        await self._append_audit(current_user.id, AuditAction.CREATE_USER, user.id, None, _snapshot(user))
        await self._session.commit()
        return UserResponse.model_validate(user)

    async def update_user(self, user_id: int, payload: UserUpdateRequest, current_user: CurrentUser) -> UserResponse:
        """Update role, account state, email, or password and audit the safe before/after state (NC-10)."""
        self._require_admin(current_user)
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise AppError(ErrorCode.USER_NOT_FOUND, "Không tìm thấy người dùng.", 404)
        before = _snapshot(user)
        await self._apply_update(user, payload)
        await self._append_audit(current_user.id, AuditAction.UPDATE_USER, user.id, before, _snapshot(user))
        await self._session.commit()
        return UserResponse.model_validate(user)

    async def _apply_update(self, user: User, payload: UserUpdateRequest) -> None:
        if payload.email is not None and str(payload.email) != user.email:
            duplicate = await self._users.get_by_email(str(payload.email))
            if duplicate is not None and duplicate.id != user.id:
                raise AppError(ErrorCode.USER_ALREADY_EXISTS, "Email đã được sử dụng.", 409)
            user.email = str(payload.email)
        if payload.password is not None:
            user.password_hash = hash_password(payload.password)
        if payload.role is not None:
            user.role = payload.role
        if payload.is_active is not None:
            user.is_active = payload.is_active

    async def _append_audit(
        self, actor_id: int, action: AuditAction, user_id: int, before: dict | None, after: dict | None
    ) -> None:
        await self._audits.create(
            AuditLog(
                user_id=actor_id,
                action=action,
                entity_type="user",
                entity_id=user_id,
                before_state=before,
                after_state=after,
            )
        )
