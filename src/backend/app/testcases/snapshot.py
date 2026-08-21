# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

from app.testcases.models import TestCase


def build_test_case_snapshot(test_case: TestCase) -> dict:
    return {
        "summary": test_case.summary,
        "preconditions": list(test_case.preconditions or []),
        "steps": list(test_case.steps or []),
        "expected_result": test_case.expected_result,
        "priority": test_case.priority.value,
        "test_techniques": list(test_case.test_techniques or []),
        "tags": list(test_case.tags or []),
        "review_note": test_case.review_note,
        "status": test_case.status.value,
        "lock_version": test_case.lock_version,
        "requirement_id": test_case.requirement_id,
        "module_id": test_case.module_id,
    }
