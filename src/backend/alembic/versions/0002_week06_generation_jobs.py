from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_week06_generation_jobs"
down_revision: str | None = "0001_week05_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    job_status = postgresql.ENUM(
        "queued",
        "running",
        "completed",
        "failed",
        name="generation_job_status",
        create_type=False,
    )
    job_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "generation_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("requirement_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("status", job_status, nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["requirement_id"],
            ["requirements.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_generation_jobs_requirement_id"),
        "generation_jobs",
        ["requirement_id"],
    )
    op.create_index(
        op.f("ix_generation_jobs_created_by"),
        "generation_jobs",
        ["created_by"],
    )
    op.create_index(
        op.f("ix_generation_jobs_status"),
        "generation_jobs",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_generation_jobs_status"),
        table_name="generation_jobs",
    )
    op.drop_index(
        op.f("ix_generation_jobs_created_by"),
        table_name="generation_jobs",
    )
    op.drop_index(
        op.f("ix_generation_jobs_requirement_id"),
        table_name="generation_jobs",
    )
    op.drop_table("generation_jobs")

    postgresql.ENUM(
        "queued",
        "running",
        "completed",
        "failed",
        name="generation_job_status",
    ).drop(op.get_bind(), checkfirst=True)
