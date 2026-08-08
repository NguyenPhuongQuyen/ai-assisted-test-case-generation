import logging
from dataclasses import dataclass

from openai import AsyncOpenAI
from pydantic import ValidationError

from app.common.config import get_settings
from app.common.constants import ErrorCode
from app.common.exceptions import AppError
from app.testcases.schemas import GeneratedTestCaseBatch

logger = logging.getLogger(__name__)


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

    async def generate_test_cases(
        self,
        requirement_text: str,
        acceptance_criteria: str | None,
    ) -> GeneratedBatchResult:
        """Generate Pydantic-validated Structured Output without exposing raw free-form model output."""
        prompt = (
            "Sinh test case từ requirement sau. Bao phủ happy path, negative scenarios, BVA/EP khi phù hợp. "
            "Không bịa quy tắc không có trong requirement; mọi giả định phải ghi vào review_note.\n\n"
            f"Requirement:\n{requirement_text}\n\nAcceptance Criteria:\n{acceptance_criteria or '(không có)'}"
        )
        try:
            response = await self._client.responses.parse(
                model=self._model,
                input=[
                    {
                        "role": "system",
                        "content": (
                            "Bạn là Senior QA Engineer. Tạo test case có cấu trúc để con người rà soát. "
                            "Đầu ra AI luôn là bản nháp và không tự phê duyệt."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                text_format=GeneratedTestCaseBatch,
                max_output_tokens=self._max_output_tokens,
            )
        except ValidationError as exc:
            logger.warning("OpenAI output failed schema validation", extra={"operation": "generate_test_cases"})
            raise AppError(ErrorCode.AI_OUTPUT_INVALID, "AI trả về dữ liệu không đúng schema.", 502) from exc
        except Exception as exc:
            logger.exception("OpenAI request failed", extra={"operation": "generate_test_cases"})
            raise AppError(ErrorCode.AI_PROVIDER_ERROR, "Không thể gọi dịch vụ AI.", 502) from exc

        parsed = response.output_parsed
        if parsed is None:
            raise AppError(ErrorCode.AI_OUTPUT_INVALID, "AI không trả về dữ liệu test case hợp lệ.", 502)

        usage = getattr(response, "usage", None)
        return GeneratedBatchResult(
            data=parsed,
            usage=AIUsage(
                input_tokens=int(getattr(usage, "input_tokens", 0) or 0),
                output_tokens=int(getattr(usage, "output_tokens", 0) or 0),
            ),
        )
