# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.common.database import Base


class TestCaseVersion(Base):
    __tablename__ = "test_case_versions"
    __table_args__ = (UniqueConstraint("test_case_id", "version_number", name="uq_test_case_versions_case_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id", ondelete="RESTRICT"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    snapshot: Mapped[dict] = mapped_column(JSON)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
