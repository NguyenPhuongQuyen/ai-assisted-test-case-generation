# Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.audit.repository import AuditLogRepository
from app.common.auth_context import CurrentUser
from app.common.constants import AuditAction, ErrorCode, TestCaseStatus, UserRole
from app.common.exceptions import AppError
from app.modules.repository import ModuleRepository
from app.requirements.models import Requirement
from app.requirements.repository import RequirementRepository
from app.requirements.schemas import RequirementCreate, RequirementUpdate
from app.testcases.repository import TestCaseRepository
from app.testcases.snapshot import build_test_case_snapshot
from app.testcases.version_repository import TestCaseVersionRepository

logger = logging.getLogger(__name__)


class RequirementService:
    def __init__(
        self,
        session: AsyncSession,
        requirements: RequirementRepository,
        modules: ModuleRepository,
        test_cases: TestCaseRepository,
        versions: TestCaseVersionRepository,
        audits: AuditLogRepository,
    ) -> None:
        self._session = session
        self._requirements = requirements
        self._modules = modules
        self._test_cases = test_cases
        self._versions = versions
        self._audits = audits

    async def create_requirement(self, payload: RequirementCreate, current_user: CurrentUser) -> Requirement:
        """Create requirement source data for an existing module.

        Args:
            payload: Validated requirement content and module reference.
            current_user: Authenticated QA user.

        Returns:
            The persisted requirement.

        Raises:
            AppError: When role or module validation fails.
        """
        self._require_qa(current_user)
        if await self._modules.get_by_id(payload.module_id) is None:
            raise AppError(ErrorCode.MODULE_NOT_FOUND, "Không tìm thấy module đã chọn.", 404)
        requirement = Requirement(
            module_id=payload.module_id,
            content=payload.content,
            acceptance_criteria=payload.acceptance_criteria,
            created_by=current_user.id,
        )
        await self._requirements.create(requirement)
        audit = self._requirement_audit(requirement, current_user, AuditAction.CREATE_REQUIREMENT, None)
        await self._audits.create(audit)
        await self._session.commit()
        logger.info(
            "Requirement created",
            extra={"requirement_id": requirement.id, "user_id": current_user.id, "operation": "create_requirement"},
        )
        return requirement

    async def list_requirements(
        self,
        module_id: int,
        page: int,
        page_size: int,
        current_user: CurrentUser,
    ) -> tuple[list[Requirement], int]:
        """List requirements owned by the current QA in one module.

        Args:
            module_id: Module used to filter requirements.
            page: One-based page number.
            page_size: Maximum records returned per page.
            current_user: Authenticated QA user.

        Returns:
            Requirement records and total matching count.

        Raises:
            AppError: When role or module validation fails.
        """
        self._require_qa(current_user)
        if await self._modules.get_by_id(module_id) is None:
            raise AppError(ErrorCode.MODULE_NOT_FOUND, "Không tìm thấy module đã chọn.", 404)

        return await self._requirements.list_by_module_and_creator(
            module_id,
            current_user.id,
            page,
            page_size,
        )

    async def update_requirement(
        self,
        requirement_id: int,
        payload: RequirementUpdate,
        current_user: CurrentUser,
    ) -> Requirement:
        """Update an owned requirement and invalidate approved/exported test cases.

        Args:
            requirement_id: Requirement identifier.
            payload: Validated mutable fields and expected lock version.
            current_user: Authenticated QA user.

        Returns:
            The updated requirement.

        Raises:
            AppError: When access, existence, or optimistic locking checks fail.
        """
        self._require_qa(current_user)
        requirement = await self._requirements.get_by_id_for_update(requirement_id)
        if requirement is None:
            raise AppError(ErrorCode.REQUIREMENT_NOT_FOUND, "Không tìm thấy requirement.", 404)
        if requirement.created_by != current_user.id:
            raise AppError(ErrorCode.FORBIDDEN_RECORD, "Bạn không có quyền sửa requirement này.", 403)
        if requirement.lock_version != payload.lock_version:
            raise AppError(ErrorCode.CONFLICT, "Requirement đã thay đổi. Vui lòng tải lại dữ liệu.", 409)
        before = self._requirement_snapshot(requirement)
        self._apply_requirement_changes(requirement, payload)
        affected_ids = await self._mark_related_cases_for_review(requirement.id, current_user.id)
        requirement.lock_version += 1
        await self._requirements.save(requirement)
        after = self._requirement_snapshot(requirement) | {"affected_test_case_ids": affected_ids}
        await self._audits.create(
            self._requirement_audit(requirement, current_user, AuditAction.UPDATE_REQUIREMENT, before, after)
        )
        await self._session.commit()
        return requirement

    async def _mark_related_cases_for_review(self, requirement_id: int, user_id: int) -> list[int]:
        # BR-08: approved/exported cases become NEEDS_FIX when their source requirement changes.
        records = await self._test_cases.list_requirement_revalidation_candidates_for_update(requirement_id)

        for test_case in records:
            test_case.status = TestCaseStatus.NEEDS_FIX
            test_case.lock_version += 1

        await self._test_cases.save_all(records)
        await self._versions.create_snapshots(
            [
                (
                    test_case.id,
                    build_test_case_snapshot(test_case),
                    user_id,
                )
                for test_case in records
            ]
        )

        return [record.id for record in records]

    @staticmethod
    def _apply_requirement_changes(requirement: Requirement, payload: RequirementUpdate) -> None:
        changes = payload.model_dump(exclude_unset=True, exclude={"lock_version"})
        for field_name, value in changes.items():
            setattr(requirement, field_name, value)

    @staticmethod
    def _requirement_snapshot(requirement: Requirement) -> dict:
        return {
            "module_id": requirement.module_id,
            "content": requirement.content,
            "acceptance_criteria": requirement.acceptance_criteria,
            "lock_version": requirement.lock_version,
        }

    def _requirement_audit(
        self,
        requirement: Requirement,
        current_user: CurrentUser,
        action: AuditAction,
        before: dict | None,
        after: dict | None = None,
    ) -> AuditLog:
        return AuditLog(
            user_id=current_user.id,
            action=action,
            entity_type="requirement",
            entity_id=requirement.id,
            before_state=before,
            after_state=after or self._requirement_snapshot(requirement),
        )

    @staticmethod
    def _require_qa(current_user: CurrentUser) -> None:
        if current_user.role != UserRole.QA:
            raise AppError(ErrorCode.FORBIDDEN_ROLE, "Chỉ Kỹ sư QA được quản lý đặc tả yêu cầu.", 403)
