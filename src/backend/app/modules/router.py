# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.repository import AuditLogRepository
from app.common.auth_context import CurrentUser, get_current_user
from app.common.database import get_session
from app.modules.coverage_repository import ModuleCoverageRepository
from app.modules.repository import ModuleRepository
from app.modules.schemas import (
    ModuleCoverageResponse,
    ModuleCreateRequest,
    ModuleListResponse,
    ModuleResponse,
    ModuleUpdateRequest,
    TestCaseTagResponse,
    TestCaseTagUpdateRequest,
)
from app.modules.service import ModuleService
from app.testcases.repository import TestCaseRepository

router = APIRouter(prefix="/modules", tags=["modules"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
ModuleIdParam = Annotated[int, Path(ge=1)]
TestCaseIdParam = Annotated[int, Path(ge=1)]
PageParam = Annotated[int, Query(ge=1)]
PageSizeParam = Annotated[int, Query(alias="pageSize", ge=1, le=100)]


def build_service(session: AsyncSession) -> ModuleService:
    return ModuleService(
        session=session,
        modules=ModuleRepository(session),
        coverage=ModuleCoverageRepository(session),
        test_cases=TestCaseRepository(session),
        audits=AuditLogRepository(session),
    )


@router.post("", response_model=ModuleResponse, status_code=status.HTTP_201_CREATED)
async def create_module(
    payload: ModuleCreateRequest,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> ModuleResponse:
    module = await build_service(session).create_module(payload, current_user)
    return ModuleResponse.model_validate(module)


@router.get("", response_model=ModuleListResponse)
async def list_modules(
    session: SessionDep,
    current_user: CurrentUserDep,
    page: PageParam = 1,
    page_size: PageSizeParam = 20,
) -> ModuleListResponse:
    del current_user  # Authentication is required; all roles need modules for requirement/test-case workflows.
    offset = (page - 1) * page_size
    items, total = await build_service(session).list_modules(offset=offset, limit=page_size)
    return ModuleListResponse(data=items, total=total, page=page, page_size=page_size)


@router.patch("/{module_id}", response_model=ModuleResponse)
async def update_module(
    module_id: ModuleIdParam,
    payload: ModuleUpdateRequest,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> ModuleResponse:
    module = await build_service(session).update_module(module_id, payload, current_user)
    return ModuleResponse.model_validate(module)


@router.patch("/{module_id}/test-cases/{test_case_id}/tags", response_model=TestCaseTagResponse)
async def update_test_case_tags(
    module_id: ModuleIdParam,
    test_case_id: TestCaseIdParam,
    payload: TestCaseTagUpdateRequest,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> TestCaseTagResponse:
    test_case = await build_service(session).update_test_case_tags(module_id, test_case_id, payload, current_user)
    return TestCaseTagResponse(id=test_case.id, module_id=test_case.module_id, tags=list(test_case.tags or []))


@router.get("/{module_id}/coverage", response_model=ModuleCoverageResponse)
async def get_module_coverage(
    module_id: ModuleIdParam,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> ModuleCoverageResponse:
    return await build_service(session).get_coverage(module_id, current_user)
