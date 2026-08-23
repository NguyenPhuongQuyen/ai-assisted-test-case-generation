"""Week 05 baseline schema.

Revision ID: 0001_week05_baseline
Revises: None
"""

# Source assistance: OpenAI ChatGPT, 2026-08-23 (AI-05).

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_week05_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _create_users_table(user_role: sa.Enum) -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column(
            "failed_login_attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])


def _create_modules_table() -> None:
    op.create_table(
        "modules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column(
            "parent_id",
            sa.Integer(),
            sa.ForeignKey("modules.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_modules_created_by", "modules", ["created_by"])


def _create_requirements_table() -> None:
    op.create_table(
        "requirements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "module_id",
            sa.Integer(),
            sa.ForeignKey("modules.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("acceptance_criteria", sa.Text(), nullable=True),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_requirements_module_id",
        "requirements",
        ["module_id"],
    )
    op.create_index(
        "ix_requirements_created_by",
        "requirements",
        ["created_by"],
    )


def _create_test_cases_table(
    test_case_priority: sa.Enum,
    test_case_status: sa.Enum,
) -> None:
    op.create_table(
        "test_cases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "requirement_id",
            sa.Integer(),
            sa.ForeignKey("requirements.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "module_id",
            sa.Integer(),
            sa.ForeignKey("modules.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("summary", sa.String(300), nullable=False),
        sa.Column("preconditions", sa.JSON(), nullable=False),
        sa.Column("steps", sa.JSON(), nullable=False),
        sa.Column("expected_result", sa.Text(), nullable=False),
        sa.Column("priority", test_case_priority, nullable=False),
        sa.Column("test_techniques", sa.JSON(), nullable=False),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("status", test_case_status, nullable=False),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    _create_test_case_indexes()


def _create_test_case_indexes() -> None:
    op.create_index(
        "ix_test_cases_requirement_id",
        "test_cases",
        ["requirement_id"],
    )
    op.create_index(
        "ix_test_cases_module_id",
        "test_cases",
        ["module_id"],
    )
    op.create_index(
        "ix_test_cases_status",
        "test_cases",
        ["status"],
    )
    op.create_index(
        "ix_test_cases_created_by",
        "test_cases",
        ["created_by"],
    )


def _create_audit_logs_table(audit_action: sa.Enum) -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("action", audit_action, nullable=False),
        sa.Column("entity_type", sa.String(80), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("before_state", sa.JSON(), nullable=True),
        sa.Column("after_state", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index(
        "ix_audit_logs_entity_id",
        "audit_logs",
        ["entity_id"],
    )
    op.create_index(
        "ix_audit_logs_created_at",
        "audit_logs",
        ["created_at"],
    )


def upgrade() -> None:
    user_role = sa.Enum("qa", "manager", "admin", name="user_role")
    test_case_priority = sa.Enum(
        "high",
        "medium",
        "low",
        name="test_case_priority",
    )
    test_case_status = sa.Enum(
        "draft",
        "in_review",
        "needs_fix",
        "approved",
        "exported",
        "rejected",
        name="test_case_status",
    )
    audit_action = sa.Enum("generate_test_cases", name="audit_action")

    _create_users_table(user_role)
    _create_modules_table()
    _create_requirements_table()
    _create_test_cases_table(test_case_priority, test_case_status)
    _create_audit_logs_table(audit_action)


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("test_cases")
    op.drop_table("requirements")
    op.drop_table("modules")
    op.drop_table("users")
    sa.Enum(name="audit_action").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="test_case_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="test_case_priority").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="user_role").drop(op.get_bind(), checkfirst=True)
