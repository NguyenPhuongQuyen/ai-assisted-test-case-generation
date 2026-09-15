import asyncio

from app.common.config import get_settings
from app.common.constants import Priority, TestCaseStatus, UserRole
from app.common.database import get_session_factory
from app.common.security import hash_password
from app.modules.models import Module
from app.requirements.models import Requirement
from app.testcases.models import TestCase
from app.testcases.version_models import TestCaseVersion
from app.users.models import User
from sqlalchemy import select


async def _get_or_create_user(
    email: str,
    role: UserRole,
    password_hash: str,
) -> User:
    session_factory = get_session_factory()

    async with session_factory() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                email=email,
                password_hash=password_hash,
                role=role,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

        return user


async def _get_or_create_module(
    session,
    *,
    name: str,
    created_by: int,
) -> Module:
    result = await session.execute(select(Module).where(Module.name == name))
    module = result.scalar_one_or_none()

    if module is None:
        module = Module(
            name=name,
            created_by=created_by,
        )
        session.add(module)
        await session.flush()

    return module


async def _get_or_create_requirement(
    session,
    *,
    module_id: int,
    content: str,
    acceptance_criteria: str,
    created_by: int,
) -> Requirement:
    result = await session.execute(
        select(Requirement).where(
            Requirement.module_id == module_id,
            Requirement.content == content,
        )
    )
    requirement = result.scalar_one_or_none()

    if requirement is None:
        requirement = Requirement(
            module_id=module_id,
            content=content,
            acceptance_criteria=acceptance_criteria,
            created_by=created_by,
        )
        session.add(requirement)
        await session.flush()

    return requirement


async def _get_or_create_test_case(
    session,
    *,
    requirement: Requirement,
    summary: str,
    preconditions: list[str],
    steps: list[str],
    expected_result: str,
    priority: Priority,
    test_techniques: list[str],
    tags: list[str],
    status: TestCaseStatus,
    review_note: str | None,
    created_by: int,
) -> TestCase:
    result = await session.execute(
        select(TestCase).where(
            TestCase.requirement_id == requirement.id,
            TestCase.summary == summary,
        )
    )
    test_case = result.scalar_one_or_none()

    if test_case is None:
        test_case = TestCase(
            requirement_id=requirement.id,
            module_id=requirement.module_id,
            summary=summary,
            preconditions=preconditions,
            steps=steps,
            expected_result=expected_result,
            priority=priority,
            test_techniques=test_techniques,
            tags=tags,
            review_note=review_note,
            status=status,
            created_by=created_by,
        )
        session.add(test_case)
        await session.flush()

    return test_case


async def _ensure_version(
    session,
    *,
    test_case: TestCase,
    created_by: int,
) -> None:
    result = await session.execute(
        select(TestCaseVersion).where(
            TestCaseVersion.test_case_id == test_case.id,
            TestCaseVersion.version_number == 1,
        )
    )

    if result.scalar_one_or_none() is not None:
        return

    snapshot = {
        "summary": test_case.summary,
        "preconditions": list(test_case.preconditions or []),
        "steps": list(test_case.steps or []),
        "expected_result": test_case.expected_result,
        "priority": test_case.priority.value,
        "test_techniques": list(test_case.test_techniques or []),
        "tags": list(test_case.tags or []),
        "review_note": test_case.review_note,
        "status": test_case.status.value,
        "requirement_id": test_case.requirement_id,
        "module_id": test_case.module_id,
        "lock_version": test_case.lock_version,
    }

    session.add(
        TestCaseVersion(
            test_case_id=test_case.id,
            version_number=1,
            snapshot=snapshot,
            created_by=created_by,
        )
    )


async def seed() -> None:
    """
    Seed a complete local demo dataset.

    This script does not call OpenAI.
    It can be used with the harmless OPENAI_API_KEY value
    from .env.example.
    """
    settings = get_settings()
    password_hash = hash_password(settings.demo_user_password)

    admin = await _get_or_create_user(
        "admin@example.com",
        UserRole.ADMIN,
        password_hash,
    )
    manager = await _get_or_create_user(
        "manager@example.com",
        UserRole.MANAGER,
        password_hash,
    )
    qa = await _get_or_create_user(
        "qa@example.com",
        UserRole.QA,
        password_hash,
    )

    session_factory = get_session_factory()

    async with session_factory() as session:
        booking = await _get_or_create_module(
            session,
            name="Booking",
            created_by=admin.id,
        )

        account = await _get_or_create_module(
            session,
            name="Account Management",
            created_by=admin.id,
        )

        booking_create = await _get_or_create_requirement(
            session,
            module_id=booking.id,
            content=("Người dùng có thể đặt phòng khi phòng còn trống trong khoảng ngày đã chọn."),
            acceptance_criteria=(
                "Đặt phòng thành công khi dữ liệu hợp lệ; "
                "không cho phép ngày trả phòng trước hoặc bằng ngày nhận phòng; "
                "không cho phép đặt phòng đã hết chỗ."
            ),
            created_by=manager.id,
        )

        booking_cancel = await _get_or_create_requirement(
            session,
            module_id=booking.id,
            content=("Người dùng có thể hủy booking hợp lệ theo chính sách hủy phòng."),
            acceptance_criteria=(
                "Booking hợp lệ được hủy thành công; "
                "booking đã hủy không được hủy lần hai; "
                "trạng thái phải được cập nhật chính xác."
            ),
            created_by=manager.id,
        )

        login_requirement = await _get_or_create_requirement(
            session,
            module_id=account.id,
            content=("Người dùng có thể đăng nhập bằng email và mật khẩu hợp lệ."),
            acceptance_criteria=(
                "Thông tin hợp lệ cho phép đăng nhập; mật khẩu sai bị từ chối; email không tồn tại không được xác thực."
            ),
            created_by=manager.id,
        )

        test_cases = [
            # Requirement 1 - Booking
            {
                "requirement": booking_create,
                "summary": "Đặt phòng thành công với dữ liệu hợp lệ",
                "preconditions": [
                    "Người dùng đã đăng nhập",
                    "Phòng còn trống",
                ],
                "steps": [
                    "Chọn phòng còn trống",
                    "Chọn ngày nhận phòng và trả phòng hợp lệ",
                    "Xác nhận đặt phòng",
                ],
                "expected_result": "Booking được tạo thành công và hiển thị mã booking.",
                "priority": Priority.HIGH,
                "test_techniques": ["Happy Path"],
                "tags": ["booking", "positive", "smoke"],
                "status": TestCaseStatus.APPROVED,
                "review_note": "Đã kiểm tra luồng chính.",
            },
            {
                "requirement": booking_create,
                "summary": "Không cho phép ngày trả phòng bằng ngày nhận phòng",
                "preconditions": [
                    "Người dùng đã đăng nhập",
                ],
                "steps": [
                    "Chọn ngày nhận phòng",
                    "Chọn ngày trả phòng bằng ngày nhận phòng",
                    "Nhấn xác nhận",
                ],
                "expected_result": "Hệ thống từ chối và hiển thị thông báo ngày không hợp lệ.",
                "priority": Priority.HIGH,
                "test_techniques": ["Boundary Value Analysis"],
                "tags": ["booking", "boundary", "date"],
                "status": TestCaseStatus.IN_REVIEW,
                "review_note": None,
            },
            {
                "requirement": booking_create,
                "summary": "Không cho phép đặt phòng đã hết chỗ",
                "preconditions": [
                    "Người dùng đã đăng nhập",
                    "Phòng đã hết chỗ",
                ],
                "steps": [
                    "Chọn phòng đã hết chỗ",
                    "Nhập thời gian hợp lệ",
                    "Nhấn xác nhận",
                ],
                "expected_result": "Hệ thống không tạo booking và thông báo phòng không còn khả dụng.",
                "priority": Priority.HIGH,
                "test_techniques": ["Negative Testing"],
                "tags": ["booking", "negative"],
                "status": TestCaseStatus.NEEDS_FIX,
                "review_note": "Cần bổ sung thông tin kiểm tra tồn kho đồng thời.",
            },
            {
                "requirement": booking_create,
                "summary": "Đặt phòng tại giá trị biên thời gian cho phép",
                "preconditions": [
                    "Người dùng đã đăng nhập",
                    "Phòng còn trống",
                ],
                "steps": [
                    "Chọn ngày đặt tại giới hạn sớm nhất hệ thống cho phép",
                    "Xác nhận booking",
                ],
                "expected_result": "Booking được chấp nhận tại đúng giá trị biên hợp lệ.",
                "priority": Priority.MEDIUM,
                "test_techniques": ["Boundary Value Analysis"],
                "tags": ["booking", "boundary"],
                "status": TestCaseStatus.DRAFT,
                "review_note": None,
            },
            # Requirement 2 - Cancel booking
            {
                "requirement": booking_cancel,
                "summary": "Hủy booking hợp lệ thành công",
                "preconditions": [
                    "Booking đang ở trạng thái có thể hủy",
                ],
                "steps": [
                    "Mở chi tiết booking",
                    "Chọn hủy booking",
                    "Xác nhận thao tác",
                ],
                "expected_result": "Booking chuyển sang trạng thái đã hủy.",
                "priority": Priority.HIGH,
                "test_techniques": ["State Transition"],
                "tags": ["booking", "cancel", "positive"],
                "status": TestCaseStatus.APPROVED,
                "review_note": "Đã duyệt.",
            },
            {
                "requirement": booking_cancel,
                "summary": "Không cho phép hủy booking lần thứ hai",
                "preconditions": [
                    "Booking đã ở trạng thái hủy",
                ],
                "steps": [
                    "Mở booking đã hủy",
                    "Thử thực hiện thao tác hủy lại",
                ],
                "expected_result": "Hệ thống từ chối thao tác hủy lần hai.",
                "priority": Priority.MEDIUM,
                "test_techniques": ["State Transition", "Negative Testing"],
                "tags": ["booking", "cancel", "negative"],
                "status": TestCaseStatus.REJECTED,
                "review_note": "Test case bị từ chối để minh họa workflow review.",
            },
            {
                "requirement": booking_cancel,
                "summary": "Hủy booking và kiểm tra trạng thái sau thao tác",
                "preconditions": [
                    "Booking hợp lệ tồn tại",
                ],
                "steps": [
                    "Hủy booking",
                    "Tải lại danh sách booking",
                    "Mở lại chi tiết booking",
                ],
                "expected_result": "Trạng thái hủy được lưu và hiển thị nhất quán.",
                "priority": Priority.MEDIUM,
                "test_techniques": ["State Transition"],
                "tags": ["booking", "cancel", "regression"],
                "status": TestCaseStatus.EXPORTED,
                "review_note": "Đã duyệt và xuất dữ liệu.",
            },
            {
                "requirement": booking_cancel,
                "summary": "Hủy booking không tồn tại",
                "preconditions": [],
                "steps": [
                    "Gửi yêu cầu hủy với booking ID không tồn tại",
                ],
                "expected_result": "Hệ thống trả lỗi phù hợp và không thay đổi dữ liệu.",
                "priority": Priority.LOW,
                "test_techniques": ["Negative Testing"],
                "tags": ["booking", "cancel", "api"],
                "status": TestCaseStatus.DRAFT,
                "review_note": None,
            },
            # Requirement 3 - Login
            {
                "requirement": login_requirement,
                "summary": "Đăng nhập thành công bằng tài khoản hợp lệ",
                "preconditions": [
                    "Tài khoản đang hoạt động",
                ],
                "steps": [
                    "Nhập email hợp lệ",
                    "Nhập mật khẩu đúng",
                    "Nhấn đăng nhập",
                ],
                "expected_result": "Người dùng đăng nhập thành công và nhận phiên xác thực.",
                "priority": Priority.HIGH,
                "test_techniques": ["Happy Path"],
                "tags": ["auth", "login", "smoke"],
                "status": TestCaseStatus.APPROVED,
                "review_note": "Luồng đăng nhập cơ bản.",
            },
            {
                "requirement": login_requirement,
                "summary": "Từ chối đăng nhập khi mật khẩu sai",
                "preconditions": [
                    "Email người dùng tồn tại",
                ],
                "steps": [
                    "Nhập email hợp lệ",
                    "Nhập mật khẩu sai",
                    "Nhấn đăng nhập",
                ],
                "expected_result": "Hệ thống từ chối đăng nhập và không tạo phiên.",
                "priority": Priority.HIGH,
                "test_techniques": ["Negative Testing"],
                "tags": ["auth", "login", "security"],
                "status": TestCaseStatus.IN_REVIEW,
                "review_note": None,
            },
            {
                "requirement": login_requirement,
                "summary": "Từ chối đăng nhập với email không tồn tại",
                "preconditions": [],
                "steps": [
                    "Nhập email chưa đăng ký",
                    "Nhập mật khẩu bất kỳ",
                    "Nhấn đăng nhập",
                ],
                "expected_result": "Hệ thống từ chối xác thực và không tạo phiên.",
                "priority": Priority.MEDIUM,
                "test_techniques": ["Equivalence Partitioning"],
                "tags": ["auth", "login", "negative"],
                "status": TestCaseStatus.NEEDS_FIX,
                "review_note": "Cần rà soát nội dung thông báo lỗi.",
            },
            {
                "requirement": login_requirement,
                "summary": "Kiểm tra định dạng email không hợp lệ",
                "preconditions": [],
                "steps": [
                    "Nhập chuỗi không đúng định dạng email",
                    "Nhập mật khẩu",
                    "Nhấn đăng nhập",
                ],
                "expected_result": "Hệ thống báo lỗi validation email.",
                "priority": Priority.LOW,
                "test_techniques": ["Equivalence Partitioning"],
                "tags": ["auth", "validation"],
                "status": TestCaseStatus.DRAFT,
                "review_note": None,
            },
        ]

        created_cases: list[TestCase] = []

        for item in test_cases:
            test_case = await _get_or_create_test_case(
                session,
                requirement=item["requirement"],
                summary=item["summary"],
                preconditions=item["preconditions"],
                steps=item["steps"],
                expected_result=item["expected_result"],
                priority=item["priority"],
                test_techniques=item["test_techniques"],
                tags=item["tags"],
                status=item["status"],
                review_note=item["review_note"],
                created_by=qa.id,
            )
            created_cases.append(test_case)

        for test_case in created_cases:
            await _ensure_version(
                session,
                test_case=test_case,
                created_by=qa.id,
            )

        await session.commit()

    print("Demo seed completed:")
    print("  Users        : 3")
    print("  Modules      : 2")
    print("  Requirements : 3")
    print("  Test cases   : 12")
    print("")
    print("Demo accounts:")
    print("  admin@example.com")
    print("  manager@example.com")
    print("  qa@example.com")
    print("")
    print("Password: value of DEMO_USER_PASSWORD in .env")


if __name__ == "__main__":
    asyncio.run(seed())
