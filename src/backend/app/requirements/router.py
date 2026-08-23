from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.repository import AuditLogRepository
from app.common.auth_context import CurrentUser, get_current_user
from app.common.database import get_session
from app.modules.repository import ModuleRepository
from app.requirements.repository import RequirementRepository
from app.requirements.schemas import RequirementCreate, RequirementResponse, RequirementUpdate
from app.requirements.service import RequirementService
from app.testcases.repository import TestCaseRepository
from app.testcases.version_repository import TestCaseVersionRepository

router = APIRouter(prefix="/requirements", tags=["requirements"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
RequirementIdParam = Annotated[int, Path(ge=1)]


def build_service(session: AsyncSession) -> RequirementService:
    return RequirementService(
        session=session,
        requirements=RequirementRepository(session),
        modules=ModuleRepository(session),
        test_cases=TestCaseRepository(session),
        versions=TestCaseVersionRepository(session),
        audits=AuditLogRepository(session),
    )


def to_response(record) -> RequirementResponse:  # type: ignore[no-untyped-def]
    return RequirementResponse(
        id=record.id,
        module_id=record.module_id,
        content=record.content,
        acceptance_criteria=record.acceptance_criteria,
        lock_version=record.lock_version,
    )


@router.post("", response_model=RequirementResponse, status_code=status.HTTP_201_CREATED)
async def create_requirement(
    payload: RequirementCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> RequirementResponse:
    record = await build_service(session).create_requirement(payload, current_user)
    return to_response(record)


@router.patch("/{requirement_id}", response_model=RequirementResponse)
async def update_requirement(
    requirement_id: RequirementIdParam,
    payload: RequirementUpdate,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> RequirementResponse:
    record = await build_service(session).update_requirement(requirement_id, payload, current_user)
    return to_response(record)
