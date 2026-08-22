# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.audit.repository import AuditLogRepository
from app.common.auth_context import CurrentUser
from app.common.constants import AuditAction, ErrorCode, UserRole
from app.common.exceptions import AppError
from app.prompt_configs.models import PromptConfig
from app.prompt_configs.repository import PromptConfigRepository
from app.prompt_configs.schemas import PromptConfigCreateRequest


class PromptConfigService:
    def __init__(
        self,
        session: AsyncSession,
        prompts: PromptConfigRepository,
        audits: AuditLogRepository,
    ) -> None:
        self._session = session
        self._prompts = prompts
        self._audits = audits

    async def create_config(self, payload: PromptConfigCreateRequest, current_user: CurrentUser) -> PromptConfig:
        """Create a new active prompt/model version while retaining previous configuration history."""
        self._require_admin(current_user)
        previous = await self._prompts.get_active()
        previous_state = self._metadata(previous) if previous is not None else None
        version_number = await self._prompts.next_version_number()
        await self._prompts.deactivate_active()
        config = PromptConfig(
            version_number=version_number,
            name=payload.name,
            system_prompt=payload.system_prompt,
            user_prompt_template=payload.user_prompt_template,
            model_name=payload.model_name,
            schema_version=payload.schema_version,
            max_output_tokens=payload.max_output_tokens,
            is_active=True,
            created_by=current_user.id,
        )
        await self._prompts.create(config)
        await self._audit_creation(config, previous_state, current_user.id)
        await self._session.commit()
        return config

    async def get_active(self, current_user: CurrentUser) -> PromptConfig:
        """Return the active prompt configuration to an authenticated administrator."""
        self._require_admin(current_user)
        config = await self._prompts.get_active()
        if config is None:
            raise AppError(ErrorCode.PROMPT_CONFIG_NOT_FOUND, "Không có cấu hình prompt đang hoạt động.", 404)
        return config

    async def list_configs(
        self,
        *,
        offset: int,
        limit: int,
        current_user: CurrentUser,
    ) -> tuple[list[PromptConfig], int]:
        """Return immutable prompt configuration history with database pagination for administrators."""
        self._require_admin(current_user)
        return await self._prompts.list_all(offset=offset, limit=limit), await self._prompts.count_all()

    async def _audit_creation(self, config: PromptConfig, previous_state: dict | None, user_id: int) -> None:
        # NC-09 / NC-11: prompt changes are versioned and auditable without duplicating full prompt text in audit logs.
        await self._audits.create(
            AuditLog(
                user_id=user_id,
                action=AuditAction.CREATE_PROMPT_CONFIG,
                entity_type="prompt_config",
                entity_id=config.id,
                before_state=previous_state,
                after_state=self._metadata(config),
            )
        )

    @staticmethod
    def _metadata(config: PromptConfig) -> dict:
        return {
            "version_number": config.version_number,
            "name": config.name,
            "model_name": config.model_name,
            "schema_version": config.schema_version,
            "max_output_tokens": config.max_output_tokens,
            "is_active": config.is_active,
        }

    @staticmethod
    def _require_admin(current_user: CurrentUser) -> None:
        # NC-09 / UC03: prompt/model configuration is restricted to administrators.
        if current_user.role != UserRole.ADMIN:
            raise AppError(ErrorCode.FORBIDDEN_ROLE, "Chỉ Admin được quản lý cấu hình prompt/model.", 403)
