# Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_nc10_user_admin"
down_revision: str | None = "0008_nc08_version_restore"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add account activation state and audit actions for NC-10 user administration."""
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.execute(sa.text("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'create_user'"))
    op.execute(sa.text("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'update_user'"))


def downgrade() -> None:
    """Remove the account activation column; PostgreSQL enum values remain append-only."""
    op.drop_column("users", "is_active")
