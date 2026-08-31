# Source assistance: OpenAI ChatGPT, 2026-08-23 (AI-05).

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_module_name_unique"
down_revision: str | None = "0009_nc10_user_admin"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Prevent duplicate module names within the same hierarchy level."""
    op.execute(
        sa.text(
            """
            CREATE UNIQUE INDEX uq_modules_root_name_ci
            ON modules (lower(name))
            WHERE parent_id IS NULL
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE UNIQUE INDEX uq_modules_parent_name_ci
            ON modules (parent_id, lower(name))
            WHERE parent_id IS NOT NULL
            """
        )
    )


def downgrade() -> None:
    """Remove case-insensitive same-level module uniqueness indexes."""
    op.drop_index(
        "uq_modules_parent_name_ci",
        table_name="modules",
    )
    op.drop_index(
        "uq_modules_root_name_ci",
        table_name="modules",
    )
