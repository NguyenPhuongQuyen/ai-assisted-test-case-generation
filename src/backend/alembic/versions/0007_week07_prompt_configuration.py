# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_week07_prompt_configuration"
down_revision: str | None = "0006_week07_module_coverage"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


DEFAULT_SYSTEM_PROMPT = (
    "Bạn là Senior QA Engineer. Tạo test case có cấu trúc để con người rà soát. "
    "Đầu ra AI luôn là bản nháp và không tự phê duyệt."
)
DEFAULT_USER_TEMPLATE = (
    "Sinh test case từ requirement sau. Bao phủ happy path, negative scenarios, BVA/EP khi phù hợp. "
    "Không bịa quy tắc không có trong requirement; mọi giả định phải ghi vào review_note.\n\n"
    "Requirement:\n{requirement_text}\n\nAcceptance Criteria:\n{acceptance_criteria}"
)


def upgrade() -> None:
    op.execute(sa.text("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'create_prompt_config'"))
    prompt_configs = op.create_table(
        "prompt_configs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("version_number", sa.Integer(), nullable=False, unique=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("user_prompt_template", sa.Text(), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("schema_version", sa.String(length=50), nullable=False),
        sa.Column("max_output_tokens", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "uq_prompt_configs_active",
        "prompt_configs",
        ["is_active"],
        unique=True,
        postgresql_where=sa.text("is_active"),
    )
    op.bulk_insert(
        prompt_configs,
        [
            {
                "version_number": 1,
                "name": "Default",
                "system_prompt": DEFAULT_SYSTEM_PROMPT,
                "user_prompt_template": DEFAULT_USER_TEMPLATE,
                "model_name": "gpt-5",
                "schema_version": "test-case-v1",
                "max_output_tokens": 4000,
                "is_active": True,
                "created_by": None,
            }
        ],
    )


def downgrade() -> None:
    op.drop_index("uq_prompt_configs_active", table_name="prompt_configs")
    op.drop_table("prompt_configs")
    # PostgreSQL enum values are retained because removing values is unsafe in a normal downgrade.
