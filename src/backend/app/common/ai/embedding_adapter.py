# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

import logging
from dataclasses import dataclass

from openai import AsyncOpenAI

from app.common.config import get_settings
from app.common.constants import ErrorCode
from app.common.exceptions import AppError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class EmbeddingBatchResult:
    vectors: list[list[float]]
    input_tokens: int


class OpenAIEmbeddingAdapter:
    """Create fixed-dimension embeddings through the shared OpenAI integration boundary."""

    def __init__(self, client: AsyncOpenAI | None = None) -> None:
        settings = get_settings()
        self._client = client or AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_embedding_model
        self._dimensions = settings.openai_embedding_dimensions

    async def embed_texts(self, texts: list[str]) -> EmbeddingBatchResult:
        """Embed one or more semantic test-case texts with configured model/dimensions.

        Args:
            texts: Non-empty semantic texts that will be compared by pgvector.

        Returns:
            Embedding vectors in input order plus provider-reported token usage.

        Raises:
            AppError: When the embedding provider cannot return valid vectors.
        """
        if not texts:
            return EmbeddingBatchResult(vectors=[], input_tokens=0)

        try:
            response = await self._client.embeddings.create(
                model=self._model,
                input=texts,
                dimensions=self._dimensions,
            )
        except Exception as exc:
            logger.exception("OpenAI embedding request failed", extra={"operation": "embed_test_cases"})
            raise AppError(ErrorCode.AI_PROVIDER_ERROR, "Không thể tạo vector embedding cho test case.", 502) from exc

        vectors = [list(item.embedding) for item in response.data]
        if len(vectors) != len(texts) or any(len(vector) != self._dimensions for vector in vectors):
            raise AppError(ErrorCode.AI_OUTPUT_INVALID, "Embedding trả về không đúng số chiều cấu hình.", 502)

        usage = getattr(response, "usage", None)
        return EmbeddingBatchResult(
            vectors=vectors,
            input_tokens=int(getattr(usage, "prompt_tokens", 0) or getattr(usage, "total_tokens", 0) or 0),
        )
