from types import SimpleNamespace
from unittest.mock import AsyncMock

import app.common.ai.openai_adapter as adapter_module
import pytest
from app.common.ai.openai_adapter import (
    MAX_SCHEMA_RETRIES,
    SCHEMA_RETRY_REMINDER,
    OpenAIAdapter,
)
from app.common.constants import ErrorCode, Priority
from app.common.exceptions import AppError
from app.testcases.schemas import GeneratedTestCase, GeneratedTestCaseBatch
from pydantic import ValidationError


def build_valid_batch() -> GeneratedTestCaseBatch:
    return GeneratedTestCaseBatch(
        test_cases=[
            GeneratedTestCase(
                summary="Check upper booking boundary",
                preconditions=["User is logged in"],
                steps=["Select 8 tickets", "Confirm booking"],
                expected_result="The system accepts exactly 8 tickets.",
                priority=Priority.HIGH,
                test_techniques=["BVA"],
                review_note=None,
            )
        ]
    )


def build_validation_error() -> ValidationError:
    with pytest.raises(ValidationError) as exc_info:
        GeneratedTestCaseBatch.model_validate({"test_cases": []})
    return exc_info.value


def build_adapter(monkeypatch, parse_mock: AsyncMock) -> OpenAIAdapter:
    settings = SimpleNamespace(
        openai_api_key="test-key",
        openai_model="test-model",
        openai_max_output_tokens=1000,
    )
    monkeypatch.setattr(adapter_module, "get_settings", lambda: settings)

    client = SimpleNamespace(
        responses=SimpleNamespace(
            parse=parse_mock,
        )
    )
    return OpenAIAdapter(client=client)


@pytest.mark.asyncio
async def test_valid_output_succeeds_without_retry(monkeypatch) -> None:
    batch = build_valid_batch()
    response = SimpleNamespace(
        output_parsed=batch,
        usage=SimpleNamespace(input_tokens=120, output_tokens=80),
    )
    parse_mock = AsyncMock(return_value=response)
    adapter = build_adapter(monkeypatch, parse_mock)

    result = await adapter.generate_test_cases(
        "User can book from 1 to 8 tickets.",
        "Nine tickets must be rejected.",
    )

    assert result.data == batch
    assert result.usage.input_tokens == 120
    assert result.usage.output_tokens == 80
    assert parse_mock.await_count == 1

    system_prompt = parse_mock.call_args.kwargs["input"][0]["content"]
    assert SCHEMA_RETRY_REMINDER not in system_prompt


@pytest.mark.asyncio
async def test_invalid_schema_is_retried_then_succeeds(monkeypatch) -> None:
    validation_error = build_validation_error()
    batch = build_valid_batch()
    valid_response = SimpleNamespace(
        output_parsed=batch,
        usage=SimpleNamespace(input_tokens=100, output_tokens=70),
    )
    parse_mock = AsyncMock(side_effect=[validation_error, valid_response])
    adapter = build_adapter(monkeypatch, parse_mock)

    result = await adapter.generate_test_cases(
        "User can book from 1 to 8 tickets.",
        None,
    )

    assert result.data == batch
    assert parse_mock.await_count == 2

    first_prompt = parse_mock.call_args_list[0].kwargs["input"][0]["content"]
    retry_prompt = parse_mock.call_args_list[1].kwargs["input"][0]["content"]
    assert SCHEMA_RETRY_REMINDER not in first_prompt
    assert SCHEMA_RETRY_REMINDER in retry_prompt


@pytest.mark.asyncio
async def test_invalid_schema_after_all_retries_returns_ai_output_invalid(
    monkeypatch,
) -> None:
    validation_error = build_validation_error()
    parse_mock = AsyncMock(side_effect=[validation_error] * (MAX_SCHEMA_RETRIES + 1))
    adapter = build_adapter(monkeypatch, parse_mock)

    with pytest.raises(AppError) as exc_info:
        await adapter.generate_test_cases(
            "User can book from 1 to 8 tickets.",
            None,
        )

    assert exc_info.value.code == ErrorCode.AI_OUTPUT_INVALID
    assert exc_info.value.status_code == 502
    assert parse_mock.await_count == MAX_SCHEMA_RETRIES + 1

    for retry_call in parse_mock.call_args_list[1:]:
        system_prompt = retry_call.kwargs["input"][0]["content"]
        assert SCHEMA_RETRY_REMINDER in system_prompt


@pytest.mark.asyncio
async def test_provider_error_is_not_retried(monkeypatch) -> None:
    parse_mock = AsyncMock(side_effect=RuntimeError("provider unavailable"))
    adapter = build_adapter(monkeypatch, parse_mock)

    with pytest.raises(AppError) as exc_info:
        await adapter.generate_test_cases(
            "User can book from 1 to 8 tickets.",
            None,
        )

    assert exc_info.value.code == ErrorCode.AI_PROVIDER_ERROR
    assert exc_info.value.status_code == 502
    assert parse_mock.await_count == 1


@pytest.mark.asyncio
async def test_missing_parsed_output_is_retried_then_fails(monkeypatch) -> None:
    empty_response = SimpleNamespace(
        output_parsed=None,
        usage=None,
    )
    parse_mock = AsyncMock(side_effect=[empty_response] * (MAX_SCHEMA_RETRIES + 1))
    adapter = build_adapter(monkeypatch, parse_mock)

    with pytest.raises(AppError) as exc_info:
        await adapter.generate_test_cases(
            "User can book from 1 to 8 tickets.",
            None,
        )

    assert exc_info.value.code == ErrorCode.AI_OUTPUT_INVALID
    assert exc_info.value.status_code == 502
    assert parse_mock.await_count == MAX_SCHEMA_RETRIES + 1
