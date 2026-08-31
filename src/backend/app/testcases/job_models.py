from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.common.constants import GenerationJobStatus
from app.common.database import Base


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    requirement_id: Mapped[int] = mapped_column(
        ForeignKey("requirements.id", ondelete="RESTRICT"),
        index=True,
    )
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
    )
    status: Mapped[GenerationJobStatus] = mapped_column(
        Enum(
            GenerationJobStatus,
            values_callable=lambda enum_class: [member.value for member in enum_class],
            name="generation_job_status",
        ),
        default=GenerationJobStatus.QUEUED,
        index=True,
    )
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
