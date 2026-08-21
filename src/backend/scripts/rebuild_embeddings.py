# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

import argparse
import asyncio
import logging

from app.common.ai.embedding_adapter import OpenAIEmbeddingAdapter
from app.common.database import get_session_factory
from app.testcases.models import TestCase
from app.testcases.repository import TestCaseRepository
from app.testcases.semantic_text import build_test_case_semantic_text
from sqlalchemy import select

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rebuild pgvector embeddings for all test cases.")
    parser.add_argument("--batch-size", type=int, default=50, choices=range(1, 101), metavar="1..100")
    return parser.parse_args()


async def rebuild_embeddings(batch_size: int) -> None:
    """Rebuild all test-case embeddings in database-sized batches.

    Args:
        batch_size: Maximum test cases sent to the embedding API per request.

    Returns:
        None. Progress is written through the Python logging library.
    """
    session_factory = get_session_factory()
    adapter = OpenAIEmbeddingAdapter()
    offset = 0
    processed = 0

    async with session_factory() as session:
        repository = TestCaseRepository(session)
        while True:
            result = await session.execute(select(TestCase).order_by(TestCase.id).offset(offset).limit(batch_size))
            rows = list(result.scalars().all())
            if not rows:
                break

            embedded = await adapter.embed_texts([build_test_case_semantic_text(item) for item in rows])
            pairs = [(item.id, vector) for item, vector in zip(rows, embedded.vectors, strict=True)]
            await repository.set_embeddings(pairs)
            await session.commit()
            processed += len(rows)
            offset += len(rows)
            logger.info("Embedding rebuild progress", extra={"processed": processed, "operation": "rebuild_embeddings"})


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    arguments = parse_args()
    asyncio.run(rebuild_embeddings(arguments.batch_size))
