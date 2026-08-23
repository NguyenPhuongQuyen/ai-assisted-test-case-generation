from app.testcases.models import TestCase


def build_test_case_semantic_text(test_case: TestCase) -> str:
    """Build stable semantic text used for duplicate similarity comparison."""
    sections = [
        f"Summary: {test_case.summary}",
        "Preconditions: " + " | ".join(test_case.preconditions),
        "Steps: " + " | ".join(test_case.steps),
        f"Expected result: {test_case.expected_result}",
    ]
    return "\n".join(sections)
