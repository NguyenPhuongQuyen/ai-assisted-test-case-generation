import pytest
from app.testcases.schemas import GeneratedTestCaseBatch
from pydantic import ValidationError


def test_structured_output_rejects_missing_required_expected_result() -> None:
    # Arrange
    invalid_payload = {
        "test_cases": [
            {
                "summary": "Missing expected result",
                "preconditions": [],
                "steps": ["Do something"],
                "priority": "high",
                "test_techniques": ["EP"],
            }
        ]
    }

    # Act / Assert
    with pytest.raises(ValidationError):
        GeneratedTestCaseBatch.model_validate(invalid_payload)
