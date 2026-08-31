# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.repository import AuditLogRepository
from app.common.auth_context import CurrentUser, get_current_user
from app.common.database import get_session
from app.prompt_configs.repository import PromptConfigRepository
from app.prompt_configs.schemas import PromptConfigCreateRequest, PromptConfigListResponse, PromptConfigResponse
from app.prompt_configs.service import PromptConfigService

router = APIRouter(prefix="/prompt-configs", tags=["prompt-configs"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
PageParam = Annotated[int, Query(ge=1)]
PageSizeParam = Annotated[int, Query(alias="pageSize", ge=1, le=100)]


def build_service(session: AsyncSession) -> PromptConfigService:
    return PromptConfigService(
        session=session,
        prompts=PromptConfigRepository(session),
        audits=AuditLogRepository(session),
    )


@router.post("", response_model=PromptConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt_config(
    payload: PromptConfigCreateRequest,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> PromptConfigResponse:
    config = await build_service(session).create_config(payload, current_user)
    return PromptConfigResponse.model_validate(config)


@router.get("/active", response_model=PromptConfigResponse)
async def get_active_prompt_config(
    session: SessionDep,
    current_user: CurrentUserDep,
) -> PromptConfigResponse:
    config = await build_service(session).get_active(current_user)
    return PromptConfigResponse.model_validate(config)


@router.get("", response_model=PromptConfigListResponse)
async def list_prompt_configs(
    session: SessionDep,
    current_user: CurrentUserDep,
    page: PageParam = 1,
    page_size: PageSizeParam = 20,
) -> PromptConfigListResponse:
    offset = (page - 1) * page_size
    items, total = await build_service(session).list_configs(
        offset=offset,
        limit=page_size,
        current_user=current_user,
    )
    return PromptConfigListResponse(data=items, total=total, page=page, page_size=page_size)
