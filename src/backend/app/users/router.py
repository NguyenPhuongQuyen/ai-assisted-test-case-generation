from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.schemas import CurrentUser
from app.common.database import get_session
from app.users.repository import UserRepository
from app.users.schemas import UserCreateRequest, UserResponse
from app.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


def build_service(session: AsyncSession) -> UserService:
    return UserService(session, UserRepository(session))


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreateRequest,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> UserResponse:
    return await build_service(session).create_user(payload, current_user)
