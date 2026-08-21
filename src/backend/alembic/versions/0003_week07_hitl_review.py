# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_week07_hitl_review"
down_revision: str | None = "0002_week06_generation_jobs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _add_audit_actions() -> None:
    op.execute(sa.text("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'edit_test_case'"))
    op.execute(sa.text("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'submit_test_case_review'"))
    op.execute(sa.text("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'request_test_case_fix'"))
    op.execute(sa.text("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'approve_test_case'"))
    op.execute(sa.text("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'reject_test_case'"))


def _create_version_table() -> None:
    op.create_table(
        "test_case_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("test_case_id", sa.Integer(), sa.ForeignKey("test_cases.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("test_case_id", "version_number", name="uq_test_case_versions_case_number"),
    )
    op.create_index("ix_test_case_versions_test_case_id", "test_case_versions", ["test_case_id"])
    op.create_index("ix_test_case_versions_created_by", "test_case_versions", ["created_by"])
    op.create_index("ix_test_case_versions_created_at", "test_case_versions", ["created_at"])


def _backfill_existing_versions() -> None:
    # BR-06: preserve an initial immutable snapshot for test cases created before this migration.
    op.execute(
        sa.text(
            """
            INSERT INTO test_case_versions (test_case_id, version_number, snapshot, created_by)
            SELECT id, 1,
                json_build_object(
                    'summary', summary, 'preconditions', preconditions, 'steps', steps,
                    'expected_result', expected_result, 'priority', priority::text,
                    'test_techniques', test_techniques, 'review_note', review_note,
                    'status', status::text, 'lock_version', lock_version,
                    'requirement_id', requirement_id, 'module_id', module_id
                ),
                created_by
            FROM test_cases
            """
        )
    )


def upgrade() -> None:
    _add_audit_actions()
    # DB-15: clients send this value back so stale human-review writes return HTTP 409.
    op.add_column("test_cases", sa.Column("lock_version", sa.Integer(), server_default="1", nullable=False))
    _create_version_table()
    _backfill_existing_versions()


def downgrade() -> None:
    op.drop_index("ix_test_case_versions_created_at", table_name="test_case_versions")
    op.drop_index("ix_test_case_versions_created_by", table_name="test_case_versions")
    op.drop_index("ix_test_case_versions_test_case_id", table_name="test_case_versions")
    op.drop_table("test_case_versions")
    op.drop_column("test_cases", "lock_version")
    # PostgreSQL enum values are retained because removing individual enum values is unsafe in a normal downgrade.
