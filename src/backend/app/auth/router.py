from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import AuthResponse, LoginRequest
from app.auth.service import AuthService
from app.common.database import get_session
from app.users.repository import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


def build_service(session: AsyncSession) -> AuthService:
    return AuthService(session, UserRepository(session))


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    session: SessionDep,
) -> AuthResponse:
    return await build_service(session).login(payload)
