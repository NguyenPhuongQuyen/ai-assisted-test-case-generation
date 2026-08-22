import logging
from dataclasses import dataclass

from openai import AsyncOpenAI
from pydantic import ValidationError

from app.common.ai.schemas import GeneratedTestCaseBatch
from app.common.config import get_settings
from app.common.constants import ErrorCode
from app.common.exceptions import AppError

logger = logging.getLogger(__name__)


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

    async def generate_test_cases(
        self,
        requirement_text: str,
        acceptance_criteria: str | None,
        prompt_config: PromptRuntimeConfig,
    ) -> GeneratedBatchResult:
        """Generate Pydantic-validated Structured Output using the active persisted prompt configuration."""
        user_prompt = prompt_config.user_prompt_template.format(
            requirement_text=requirement_text,
            acceptance_criteria=acceptance_criteria or "(không có)",
        )
        try:
            response = await self._client.responses.parse(
                model=prompt_config.model_name,
                input=[
                    {"role": "system", "content": prompt_config.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                text_format=GeneratedTestCaseBatch,
                max_output_tokens=prompt_config.max_output_tokens,
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
