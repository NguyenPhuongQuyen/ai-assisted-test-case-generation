import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import CurrentUser
from app.common.constants import ErrorCode, UserRole
from app.common.exceptions import AppError
from app.modules.repository import ModuleRepository
from app.requirements.models import Requirement
from app.requirements.repository import RequirementRepository
from app.requirements.schemas import RequirementCreate

logger = logging.getLogger(__name__)


class RequirementService:
    def __init__(
        self,
        session: AsyncSession,
        requirements: RequirementRepository,
        modules: ModuleRepository,
    ) -> None:
        self._session = session
        self._requirements = requirements
        self._modules = modules

    async def create_requirement(self, payload: RequirementCreate, current_user: CurrentUser) -> Requirement:
        """Create SRS prose for an existing module; raises 403/404 when role or module is invalid."""
        if current_user.role != UserRole.QA:
            raise AppError(ErrorCode.FORBIDDEN_ROLE, "Chỉ Kỹ sư QA được nhập đặc tả yêu cầu.", 403)

        if await self._modules.get_by_id(payload.module_id) is None:
            raise AppError(ErrorCode.MODULE_NOT_FOUND, "Không tìm thấy module đã chọn.", 404)

        requirement = Requirement(
            module_id=payload.module_id,
            content=payload.content,
            acceptance_criteria=payload.acceptance_criteria,
            created_by=current_user.id,
        )
        await self._requirements.create(requirement)
        await self._session.commit()
        logger.info(
            "Requirement created",
            extra={"requirement_id": requirement.id, "user_id": current_user.id, "operation": "create_requirement"},
        )
        return requirement
