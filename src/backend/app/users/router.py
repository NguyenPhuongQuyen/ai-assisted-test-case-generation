# Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.repository import AuditLogRepository
from app.auth.dependencies import get_current_user
from app.auth.schemas import CurrentUser
from app.common.database import get_session
from app.users.repository import UserRepository
from app.users.schemas import UserCreateRequest, UserListResponse, UserResponse, UserUpdateRequest
from app.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
PageParam = Annotated[int, Query(ge=1)]
PageSizeParam = Annotated[int, Query(alias="pageSize", ge=1, le=100)]


def build_service(session: AsyncSession) -> UserService:
    return UserService(session, UserRepository(session), AuditLogRepository(session))


@router.get("", response_model=UserListResponse)
async def list_users(
    session: SessionDep, current_user: CurrentUserDep, page: PageParam = 1, page_size: PageSizeParam = 20
) -> UserListResponse:
    return await build_service(session).list_users(page, page_size, current_user)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreateRequest, session: SessionDep, current_user: CurrentUserDep) -> UserResponse:
    return await build_service(session).create_user(payload, current_user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, payload: UserUpdateRequest, session: SessionDep, current_user: CurrentUserDep
) -> UserResponse:
    return await build_service(session).update_user(user_id, payload, current_user)
