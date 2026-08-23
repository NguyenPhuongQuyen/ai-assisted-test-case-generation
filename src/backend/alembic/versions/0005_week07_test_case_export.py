# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_week07_test_case_export"
down_revision: str | None = "0004_week07_pgvector_duplicates"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # BR-06 / NC-11: export operations need a dedicated append-only audit action.
    op.execute(sa.text("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'export_test_cases'"))


def downgrade() -> None:
    # PostgreSQL enum values are retained because removing one value is unsafe in a normal downgrade.
    pass
