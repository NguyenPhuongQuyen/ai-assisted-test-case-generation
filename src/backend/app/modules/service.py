# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.audit.repository import AuditLogRepository
from app.auth.schemas import CurrentUser
from app.common.constants import AuditAction, ErrorCode, UserRole
from app.common.exceptions import AppError
from app.modules.coverage_repository import ModuleCoverageRepository
from app.modules.models import Module
from app.modules.repository import ModuleRepository
from app.modules.schemas import (
    ModuleCoverageResponse,
    ModuleCreateRequest,
    ModuleUpdateRequest,
    TestCaseTagUpdateRequest,
)
from app.testcases.models import TestCase
from app.testcases.repository import TestCaseRepository


class ModuleService:
    def __init__(
        self,
        session: AsyncSession,
        modules: ModuleRepository,
        coverage: ModuleCoverageRepository,
        test_cases: TestCaseRepository,
        audits: AuditLogRepository,
    ) -> None:
        self._session = session
        self._modules = modules
        self._coverage = coverage
        self._test_cases = test_cases
        self._audits = audits

    async def create_module(self, payload: ModuleCreateRequest, current_user: CurrentUser) -> Module:
        """Create a module for an authenticated test manager after validating its parent and name."""
        self._require_manager(current_user)
        await self._validate_parent(parent_id=payload.parent_id, module_id=None)
        await self._reject_duplicate_name(payload.name, payload.parent_id, exclude_id=None)
        module = Module(name=payload.name, parent_id=payload.parent_id, created_by=current_user.id)
        try:
            await self._modules.create(module)
        except IntegrityError as exc:
            await self._session.rollback()
            raise AppError(
                ErrorCode.CONFLICT,
                "Tên module đã tồn tại trong cùng cấp.",
                409,
            ) from exc
        await self._record_module_audit(AuditAction.CREATE_MODULE, module, current_user, before_state=None)
        await self._session.commit()
        return module

    async def update_module(
        self,
        module_id: int,
        payload: ModuleUpdateRequest,
        current_user: CurrentUser,
    ) -> Module:
        """Update module metadata while preventing missing parents, duplicates, and parent cycles."""
        self._require_manager(current_user)
        module = await self._require_module(module_id)
        changes = payload.model_dump(exclude_unset=True)
        if not changes:
            raise AppError(ErrorCode.VALIDATION_ERROR, "Không có dữ liệu thay đổi.", 422)
        new_name = changes.get("name", module.name)
        new_parent_id = changes.get("parent_id", module.parent_id)
        await self._validate_parent(parent_id=new_parent_id, module_id=module.id)
        await self._reject_duplicate_name(new_name, new_parent_id, exclude_id=module.id)
        before = self._module_state(module)
        module.name = new_name
        module.parent_id = new_parent_id
        try:
            await self._modules.save(module)
        except IntegrityError as exc:
            await self._session.rollback()
            raise AppError(
                ErrorCode.CONFLICT,
                "Tên module đã tồn tại trong cùng cấp.",
                409,
            ) from exc
        await self._record_module_audit(AuditAction.UPDATE_MODULE, module, current_user, before_state=before)
        await self._session.commit()
        return module

    async def list_modules(self, *, offset: int, limit: int) -> tuple[list[Module], int]:
        """Return a database-paginated module list for authenticated callers."""
        return await self._modules.list_all(offset=offset, limit=limit), await self._modules.count_all()

    async def update_test_case_tags(
        self,
        module_id: int,
        test_case_id: int,
        payload: TestCaseTagUpdateRequest,
        current_user: CurrentUser,
    ) -> TestCase:
        """Assign normalized organization tags to a test case in the selected module."""
        self._require_manager(current_user)
        await self._require_module(module_id)
        test_case = await self._test_cases.get_by_id(test_case_id)
        if test_case is None:
            raise AppError(ErrorCode.TEST_CASE_NOT_FOUND, "Không tìm thấy test case.", 404)
        if test_case.module_id != module_id:
            raise AppError(ErrorCode.FORBIDDEN_RECORD, "Test case không thuộc module đã chọn.", 403)
        # NC-06 / NC-11: organization tags are manager-controlled and every change is auditable.
        before = {"tags": list(test_case.tags or [])}
        test_case.tags = list(payload.tags)
        await self._test_cases.save(test_case)
        await self._audits.create(
            AuditLog(
                user_id=current_user.id,
                action=AuditAction.TAG_TEST_CASE,
                entity_type="test_case",
                entity_id=test_case.id,
                before_state=before,
                after_state={"tags": list(test_case.tags)},
            )
        )
        await self._session.commit()
        return test_case

    async def get_coverage(self, module_id: int, current_user: CurrentUser) -> ModuleCoverageResponse:
        """Return NC-12 requirement/test-case statistics scoped by the caller role."""
        await self._require_module(module_id)
        if current_user.role not in {UserRole.QA, UserRole.MANAGER}:
            raise AppError(ErrorCode.FORBIDDEN_ROLE, "Chỉ QA hoặc Manager được xem độ bao phủ.", 403)
        # NC-12 / BR-07: QA statistics are record-scoped; managers see module-wide statistics.
        owner_id = current_user.id if current_user.role == UserRole.QA else None
        record = await self._coverage.get_coverage(module_id=module_id, owner_id=owner_id)
        percentage = 0.0
        if record.total_requirements:
            percentage = round(record.covered_requirements * 100 / record.total_requirements, 2)
        return ModuleCoverageResponse(
            module_id=module_id,
            total_requirements=record.total_requirements,
            covered_requirements=record.covered_requirements,
            requirement_coverage_percent=percentage,
            total_test_cases=record.total_test_cases,
            approved_test_cases=record.approved_test_cases,
            status_counts=record.status_counts,
        )

    async def _validate_parent(self, *, parent_id: int | None, module_id: int | None) -> None:
        # NC-06 / UC04: parent references must exist and must not create cycles in the module tree.
        if parent_id is None:
            return
        if module_id is not None and parent_id == module_id:
            raise AppError(ErrorCode.VALIDATION_ERROR, "Module không thể là parent của chính nó.", 422)
        parent = await self._modules.get_by_id(parent_id)
        if parent is None:
            raise AppError(ErrorCode.MODULE_NOT_FOUND, "Không tìm thấy parent module.", 404)
        visited: set[int] = set()
        while parent.parent_id is not None:
            if parent.id in visited or (module_id is not None and parent.parent_id == module_id):
                raise AppError(ErrorCode.VALIDATION_ERROR, "Parent module tạo vòng lặp cây.", 422)
            visited.add(parent.id)
            parent = await self._modules.get_by_id(parent.parent_id)
            if parent is None:
                break

    async def _reject_duplicate_name(self, name: str, parent_id: int | None, exclude_id: int | None) -> None:
        if await self._modules.exists_with_name(name=name, parent_id=parent_id, exclude_id=exclude_id):
            raise AppError(ErrorCode.CONFLICT, "Tên module đã tồn tại trong cùng cấp.", 409)

    async def _require_module(self, module_id: int) -> Module:
        module = await self._modules.get_by_id(module_id)
        if module is None:
            raise AppError(ErrorCode.MODULE_NOT_FOUND, "Không tìm thấy module.", 404)
        return module

    async def _record_module_audit(
        self,
        action: AuditAction,
        module: Module,
        current_user: CurrentUser,
        *,
        before_state: dict | None,
    ) -> None:
        await self._audits.create(
            AuditLog(
                user_id=current_user.id,
                action=action,
                entity_type="module",
                entity_id=module.id,
                before_state=before_state,
                after_state=self._module_state(module),
            )
        )

    @staticmethod
    def _module_state(module: Module) -> dict:
        return {"name": module.name, "parent_id": module.parent_id}

    @staticmethod
    def _require_manager(current_user: CurrentUser) -> None:
        # NC-06 / UC04: test organization is a Manager responsibility in the SRS.
        if current_user.role != UserRole.MANAGER:
            raise AppError(ErrorCode.FORBIDDEN_ROLE, "Chỉ Manager được quản lý module và tag.", 403)
