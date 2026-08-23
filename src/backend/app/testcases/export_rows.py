# Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).

from app.testcases.models import TestCase


def to_export_row(test_case: TestCase) -> list[str | int]:
    """Convert one test case entity into an export-safe row."""
    return [
        test_case.id,
        test_case.requirement_id,
        test_case.module_id,
        safe_cell(test_case.summary),
        safe_cell(join_numbered_steps(test_case.preconditions)),
        safe_cell(join_numbered_steps(test_case.steps)),
        safe_cell(test_case.expected_result),
        test_case.priority.value,
        safe_cell(", ".join(test_case.test_techniques)),
        safe_cell(test_case.review_note or ""),
        test_case.status.value,
        test_case.created_by,
        test_case.created_at.isoformat(),
    ]


def join_numbered_steps(values: list[str]) -> str:
    """Render values as one-based numbered lines."""
    return "\n".join(f"{index}. {value}" for index, value in enumerate(values, start=1))


def safe_cell(value: str) -> str:
    """Neutralize spreadsheet formula prefixes in user-controlled text."""
    if value.startswith(("=", "+", "-", "@")):
        return "'" + value
    return value
