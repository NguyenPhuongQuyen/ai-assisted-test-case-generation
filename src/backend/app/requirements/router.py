from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.schemas import CurrentUser
from app.common.database import get_session
from app.modules.repository import ModuleRepository
from app.requirements.repository import RequirementRepository
from app.requirements.schemas import RequirementCreate, RequirementResponse
from app.requirements.service import RequirementService

router = APIRouter(prefix="/requirements", tags=["requirements"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


def build_service(session: AsyncSession) -> RequirementService:
    return RequirementService(session, RequirementRepository(session), ModuleRepository(session))


@router.post("", response_model=RequirementResponse, status_code=status.HTTP_201_CREATED)
async def create_requirement(
    payload: RequirementCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> RequirementResponse:
    record = await build_service(session).create_requirement(payload, current_user)
    return RequirementResponse(
        id=record.id,
        module_id=record.module_id,
        content=record.content,
        acceptance_criteria=record.acceptance_criteria,
    )
