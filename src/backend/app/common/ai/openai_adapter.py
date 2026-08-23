import logging
from dataclasses import dataclass
from typing import NoReturn

from openai import AsyncOpenAI
from pydantic import ValidationError

from app.common.config import get_settings
from app.common.constants import ErrorCode
from app.common.exceptions import AppError
from app.testcases.schemas import GeneratedTestCaseBatch

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


class OpenAIAdapter:
    """Single external integration boundary for OpenAI API (AR-11)."""

    def __init__(self, client: AsyncOpenAI | None = None) -> None:
        settings = get_settings()
        self._client = client or AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model
        self._max_output_tokens = settings.openai_max_output_tokens

    async def _parse_response(
        self,
        prompt: str,
        *,
        schema_reminder: bool,
    ):
        system_prompt = (
            "Bạn là Senior QA Engineer. Tạo test case có cấu trúc để con người rà soát. "
            "Đầu ra AI luôn là bản nháp và không tự phê duyệt."
        )

        if schema_reminder:
            system_prompt = f"{system_prompt} {SCHEMA_RETRY_REMINDER}"

        return await self._client.responses.parse(
            model=self._model,
            input=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            text_format=GeneratedTestCaseBatch,
            max_output_tokens=self._max_output_tokens,
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

    async def _request_with_schema_retry(self, prompt: str):
        last_validation_error: ValidationError | None = None

        for attempt in range(MAX_SCHEMA_RETRIES + 1):
            try:
                response = await self._parse_response(
                    prompt,
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
    ) -> GeneratedBatchResult:
        """Generate Pydantic-validated Structured Output without exposing raw free-form model output."""
        prompt = (
            "Sinh test case từ requirement sau. Bao phủ happy path, negative scenarios, BVA/EP khi phù hợp. "
            "Không bịa quy tắc không có trong requirement; mọi giả định phải ghi vào review_note.\n\n"
            f"Requirement:\n{requirement_text}\n\n"
            f"Acceptance Criteria:\n{acceptance_criteria or '(không có)'}"
        )

        response = await self._request_with_schema_retry(prompt)
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
