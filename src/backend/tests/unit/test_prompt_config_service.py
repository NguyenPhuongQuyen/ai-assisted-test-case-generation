# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.auth.schemas import CurrentUser
from app.common.constants import AuditAction, ErrorCode, UserRole
from app.common.exceptions import AppError
from app.prompt_configs.schemas import PromptConfigCreateRequest
from app.prompt_configs.service import PromptConfigService
from pydantic import ValidationError


def make_payload() -> PromptConfigCreateRequest:
    return PromptConfigCreateRequest(
        name="QA generation v2",
        system_prompt="You are a senior QA engineer. Produce structured drafts for human review.",
        user_prompt_template=(
            "Requirement:\n{requirement_text}\n\n"
            "Acceptance Criteria:\n{acceptance_criteria}\n\nGenerate boundary and negative scenarios when justified."
        ),
        model_name="gpt-5",
        schema_version="test-case-v1",
        max_output_tokens=4000,
    )


def build_service(*, active: object | None = None) -> tuple[PromptConfigService, SimpleNamespace]:
    session = AsyncMock()
    prompts = SimpleNamespace(
        get_active=AsyncMock(return_value=active),
        next_version_number=AsyncMock(return_value=2),
        deactivate_active=AsyncMock(),
        create=AsyncMock(),
        list_all=AsyncMock(return_value=[]),
        count_all=AsyncMock(return_value=0),
    )

    async def assign_id(config):  # type: ignore[no-untyped-def]
        config.id = 12
        return config

    prompts.create.side_effect = assign_id
    audits = SimpleNamespace(create=AsyncMock())
    return PromptConfigService(session, prompts, audits), SimpleNamespace(
        session=session,
        prompts=prompts,
        audits=audits,
    )


@pytest.mark.asyncio
async def test_admin_creates_new_active_version_and_audit() -> None:
    previous = SimpleNamespace(
        id=1,
        version_number=1,
        name="Default",
        model_name="gpt-5",
        schema_version="test-case-v1",
        max_output_tokens=4000,
        is_active=True,
    )
    service, deps = build_service(active=previous)

    result = await service.create_config(make_payload(), CurrentUser(id=5, role=UserRole.ADMIN))

    assert result.version_number == 2
    assert result.is_active is True
    assert result.created_by == 5
    deps.prompts.deactivate_active.assert_awaited_once()
    deps.prompts.create.assert_awaited_once()
    deps.audits.create.assert_awaited_once()
    audit_entry = deps.audits.create.await_args.args[0]
    assert audit_entry.action == AuditAction.CREATE_PROMPT_CONFIG
    deps.session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_non_admin_cannot_create_prompt_config() -> None:
    service, deps = build_service()

    with pytest.raises(AppError) as exc_info:
        await service.create_config(make_payload(), CurrentUser(id=7, role=UserRole.MANAGER))

    assert exc_info.value.code == ErrorCode.FORBIDDEN_ROLE
    deps.prompts.create.assert_not_awaited()
    deps.session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_admin_gets_active_prompt_config() -> None:
    active = SimpleNamespace(id=4)
    service, deps = build_service(active=active)

    result = await service.get_active(CurrentUser(id=5, role=UserRole.ADMIN))

    assert result is active
    deps.prompts.get_active.assert_awaited_once()


@pytest.mark.asyncio
async def test_missing_active_prompt_returns_not_found() -> None:
    service, _ = build_service(active=None)

    with pytest.raises(AppError) as exc_info:
        await service.get_active(CurrentUser(id=5, role=UserRole.ADMIN))

    assert exc_info.value.code == ErrorCode.PROMPT_CONFIG_NOT_FOUND


def test_prompt_template_requires_both_placeholders() -> None:
    with pytest.raises(ValidationError):
        PromptConfigCreateRequest(
            name="Invalid prompt",
            system_prompt="This system prompt is long enough for validation.",
            user_prompt_template="Requirement only: {requirement_text}",
            model_name="gpt-5",
            schema_version="test-case-v1",
            max_output_tokens=4000,
        )
