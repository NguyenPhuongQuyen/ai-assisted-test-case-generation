import logging
from dataclasses import dataclass
from typing import NoReturn

from openai import AsyncOpenAI
from pydantic import ValidationError

from app.common.ai.schemas import GeneratedTestCaseBatch
from app.common.config import get_settings
from app.common.constants import ErrorCode
from app.common.exceptions import AppError

logger = logging.getLogger(__name__)

# BR-04: output sai schema được phép sinh lại tối đa 2 lần.
MAX_SCHEMA_RETRIES = 2

SCHEMA_RETRY_REMINDER = (
    "Lần trả lời trước không đúng Structured Output schema. "
    "Hãy tạo lại dữ liệu và tuân thủ chính xác schema được yêu cầu."
)


@dataclass(frozen=True, slots=True)
class AIUsage:
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True, slots=True)
class GeneratedBatchResult:
    data: GeneratedTestCaseBatch
    usage: AIUsage


@dataclass(frozen=True, slots=True)
class PromptRuntimeConfig:
    version_number: int
    model_name: str
    schema_version: str
    system_prompt: str
    user_prompt_template: str
    max_output_tokens: int


class OpenAIAdapter:
    """Single external integration boundary for OpenAI API (AR-11)."""

    def __init__(self, client: AsyncOpenAI | None = None) -> None:
        settings = get_settings()
        self._client = client or AsyncOpenAI(api_key=settings.openai_api_key)

    async def _parse_response(
        self,
        user_prompt: str,
        prompt_config: PromptRuntimeConfig,
        *,
        schema_reminder: bool,
    ):
        system_prompt = prompt_config.system_prompt

        if schema_reminder:
            system_prompt = f"{system_prompt} {SCHEMA_RETRY_REMINDER}"

        return await self._client.responses.parse(
            model=prompt_config.model_name,
            input=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            text_format=GeneratedTestCaseBatch,
            max_output_tokens=prompt_config.max_output_tokens,
        )

    @staticmethod
    def _log_schema_failure(attempt: int) -> None:
        logger.warning(
            "OpenAI output failed schema validation",
            extra={
                "operation": "generate_test_cases",
                "attempt": attempt,
            },
        )

    @staticmethod
    def _raise_provider_error(exc: Exception, attempt: int) -> NoReturn:
        logger.exception(
            "OpenAI request failed",
            extra={
                "operation": "generate_test_cases",
                "attempt": attempt,
            },
        )
        raise AppError(
            ErrorCode.AI_PROVIDER_ERROR,
            "Không thể gọi dịch vụ AI.",
            502,
        ) from exc

    async def _request_with_schema_retry(
        self,
        user_prompt: str,
        prompt_config: PromptRuntimeConfig,
    ):
        last_validation_error: ValidationError | None = None

        for attempt in range(MAX_SCHEMA_RETRIES + 1):
            try:
                response = await self._parse_response(
                    user_prompt,
                    prompt_config,
                    schema_reminder=attempt > 0,
                )
            except ValidationError as exc:
                last_validation_error = exc
                self._log_schema_failure(attempt + 1)
                continue
            except Exception as exc:
                self._raise_provider_error(exc, attempt + 1)

            if response.output_parsed is not None:
                return response

            logger.warning(
                "OpenAI returned no parsed structured output",
                extra={
                    "operation": "generate_test_cases",
                    "attempt": attempt + 1,
                },
            )

        error = AppError(
            ErrorCode.AI_OUTPUT_INVALID,
            "AI trả về dữ liệu không đúng schema sau khi thử lại.",
            502,
        )

        if last_validation_error is not None:
            raise error from last_validation_error

        raise error

    async def generate_test_cases(
        self,
        requirement_text: str,
        acceptance_criteria: str | None,
        prompt_config: PromptRuntimeConfig,
    ) -> GeneratedBatchResult:
        """Generate Structured Output using the active persisted prompt configuration."""
        user_prompt = prompt_config.user_prompt_template.format(
            requirement_text=requirement_text,
            acceptance_criteria=acceptance_criteria or "(không có)",
        )

        response = await self._request_with_schema_retry(
            user_prompt,
            prompt_config,
        )
        parsed = response.output_parsed

        if parsed is None:
            raise AppError(
                ErrorCode.AI_OUTPUT_INVALID,
                "AI không trả về dữ liệu test case hợp lệ.",
                502,
            )

        usage = getattr(response, "usage", None)

        return GeneratedBatchResult(
            data=parsed,
            usage=AIUsage(
                input_tokens=int(getattr(usage, "input_tokens", 0) or 0),
                output_tokens=int(getattr(usage, "output_tokens", 0) or 0),
            ),
        )
