# Source assistance: OpenAI ChatGPT, 2026-08-23 (AI-05).

from pydantic import BaseModel, ConfigDict, Field

from app.common.constants import Priority


class GeneratedTestCase(BaseModel):
    """Structured test-case output returned by the AI provider."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=3, max_length=300)
    preconditions: list[str] = Field(default_factory=list, max_length=20)
    steps: list[str] = Field(min_length=1, max_length=30)
    expected_result: str = Field(min_length=3, max_length=1000)
    priority: Priority
    test_techniques: list[str] = Field(
        default_factory=list,
        max_length=10,
    )
    review_note: str | None = Field(
        default=None,
        max_length=1000,
    )


class GeneratedTestCaseBatch(BaseModel):
    """Validated batch of structured test cases returned by AI."""

    model_config = ConfigDict(extra="forbid")

    test_cases: list[GeneratedTestCase] = Field(
        min_length=1,
        max_length=50,
    )
