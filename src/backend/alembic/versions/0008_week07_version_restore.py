# Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_nc08_version_restore"
down_revision: str | None = "0007_week07_prompt_configuration"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("requirements", sa.Column("lock_version", sa.Integer(), server_default="1", nullable=False))
    op.execute(sa.text("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'create_requirement'"))
    op.execute(sa.text("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'update_requirement'"))
    op.execute(sa.text("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'restore_test_case'"))


def downgrade() -> None:
    op.drop_column("requirements", "lock_version")
    # PostgreSQL enum values are retained because removing values is unsafe in a normal downgrade.
