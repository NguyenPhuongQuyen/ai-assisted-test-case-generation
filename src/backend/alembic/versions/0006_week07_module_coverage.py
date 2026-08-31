# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_week07_module_coverage"
down_revision: str | None = "0005_week07_test_case_export"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # NC-06: tags are organization metadata and default to an empty list for existing test cases.
    op.add_column(
        "test_cases",
        sa.Column("tags", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
    )
    op.execute(sa.text("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'create_module'"))
    op.execute(sa.text("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'update_module'"))
    op.execute(sa.text("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'tag_test_case'"))


def downgrade() -> None:
    op.drop_column("test_cases", "tags")
    # PostgreSQL enum values are retained because removing values is unsafe in a normal downgrade.
