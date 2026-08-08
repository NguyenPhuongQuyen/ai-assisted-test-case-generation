from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.common.constants import Priority, TestCaseStatus
from app.common.database import Base


def _enum_values(enum_class: type[StrEnum]) -> list[str]:
    return [member.value for member in enum_class]


class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    requirement_id: Mapped[int] = mapped_column(ForeignKey("requirements.id", ondelete="RESTRICT"), index=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id", ondelete="RESTRICT"), index=True)
    summary: Mapped[str] = mapped_column(String(300))
    preconditions: Mapped[list[str]] = mapped_column(JSON, default=list)
    steps: Mapped[list[str]] = mapped_column(JSON)
    expected_result: Mapped[str] = mapped_column(Text)
    priority: Mapped[Priority] = mapped_column(Enum(Priority, values_callable=_enum_values, name="test_case_priority"))
    test_techniques: Mapped[list[str]] = mapped_column(JSON, default=list)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TestCaseStatus] = mapped_column(
        Enum(TestCaseStatus, values_callable=_enum_values, name="test_case_status"),
        default=TestCaseStatus.DRAFT,
        index=True,
    )
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
