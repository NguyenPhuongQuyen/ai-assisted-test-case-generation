# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_week07_pgvector_duplicates"
down_revision: str | None = "0003_week07_hitl_review"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


EMBEDDING_DIMENSIONS = 1536


def upgrade() -> None:
    # DB-12 / NC-05: PostgreSQL remains the primary database; pgvector adds semantic duplicate search.
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
    op.execute(sa.text(f"ALTER TABLE test_cases ADD COLUMN embedding vector({EMBEDDING_DIMENSIONS})"))
    op.execute(
        sa.text(
            "CREATE INDEX ix_test_cases_embedding_hnsw "
            "ON test_cases USING hnsw (embedding vector_cosine_ops) "
            "WHERE embedding IS NOT NULL"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS ix_test_cases_embedding_hnsw"))
    op.execute(sa.text("ALTER TABLE test_cases DROP COLUMN IF EXISTS embedding"))
    # The vector extension is retained because another database object may use it later.
