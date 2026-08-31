# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

from dataclasses import dataclass

from sqlalchemy import case, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import Priority, TestCaseStatus
from app.testcases.models import TestCase

_DUPLICATE_LIST_ALL = """
    WITH target AS (
        SELECT embedding
        FROM test_cases
        WHERE id = :test_case_id
    )
    SELECT
        candidate.id,
        candidate.requirement_id,
        candidate.summary,
        candidate.status::text AS status,
        candidate.priority::text AS priority,
        1 - (candidate.embedding <=> target.embedding) AS similarity
    FROM test_cases AS candidate
    CROSS JOIN target
    WHERE target.embedding IS NOT NULL
      AND candidate.id <> :test_case_id
      AND candidate.module_id = :module_id
      AND candidate.embedding IS NOT NULL
      AND candidate.status::text <> 'rejected'
      AND (candidate.embedding <=> target.embedding) <= :max_distance
    ORDER BY candidate.embedding <=> target.embedding
    LIMIT :limit OFFSET :offset
"""

_DUPLICATE_LIST_OWNER = """
    WITH target AS (
        SELECT embedding
        FROM test_cases
        WHERE id = :test_case_id
    )
    SELECT
        candidate.id,
        candidate.requirement_id,
        candidate.summary,
        candidate.status::text AS status,
        candidate.priority::text AS priority,
        1 - (candidate.embedding <=> target.embedding) AS similarity
    FROM test_cases AS candidate
    CROSS JOIN target
    WHERE target.embedding IS NOT NULL
      AND candidate.id <> :test_case_id
      AND candidate.module_id = :module_id
      AND candidate.embedding IS NOT NULL
      AND candidate.status::text <> 'rejected'
      AND (candidate.embedding <=> target.embedding) <= :max_distance
      AND candidate.created_by = :owner_id
    ORDER BY candidate.embedding <=> target.embedding
    LIMIT :limit OFFSET :offset
"""

_DUPLICATE_COUNT_ALL = """
    WITH target AS (
        SELECT embedding
        FROM test_cases
        WHERE id = :test_case_id
    )
    SELECT COUNT(*)
    FROM test_cases AS candidate
    CROSS JOIN target
    WHERE target.embedding IS NOT NULL
      AND candidate.id <> :test_case_id
      AND candidate.module_id = :module_id
      AND candidate.embedding IS NOT NULL
      AND candidate.status::text <> 'rejected'
      AND (candidate.embedding <=> target.embedding) <= :max_distance
"""

_DUPLICATE_COUNT_OWNER = """
    WITH target AS (
        SELECT embedding
        FROM test_cases
        WHERE id = :test_case_id
    )
    SELECT COUNT(*)
    FROM test_cases AS candidate
    CROSS JOIN target
    WHERE target.embedding IS NOT NULL
      AND candidate.id <> :test_case_id
      AND candidate.module_id = :module_id
      AND candidate.embedding IS NOT NULL
      AND candidate.status::text <> 'rejected'
      AND (candidate.embedding <=> target.embedding) <= :max_distance
      AND candidate.created_by = :owner_id
"""


_DUPLICATE_PAIR_SIMILARITY = """
    SELECT
        1 - (candidate.embedding <=> target.embedding) AS similarity
    FROM test_cases AS target
    JOIN test_cases AS candidate ON candidate.id = :source_id
    WHERE target.id = :target_id
      AND candidate.id <> target.id
      AND candidate.module_id = target.module_id
      AND target.embedding IS NOT NULL
      AND candidate.embedding IS NOT NULL
      AND target.status::text <> 'rejected'
      AND candidate.status::text <> 'rejected'
"""


@dataclass(frozen=True, slots=True)
class DuplicateCandidateRecord:
    id: int
    requirement_id: int
    summary: str
    status: TestCaseStatus
    priority: Priority
    similarity: float


class TestCaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_many(self, test_cases: list[TestCase]) -> list[TestCase]:
        self._session.add_all(test_cases)
        await self._session.flush()
        return test_cases

    async def get_by_id(self, test_case_id: int) -> TestCase | None:
        result = await self._session.execute(select(TestCase).where(TestCase.id == test_case_id))
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, test_case_id: int) -> TestCase | None:
        statement = select(TestCase).where(TestCase.id == test_case_id).with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def save(self, test_case: TestCase) -> TestCase:
        self._session.add(test_case)
        await self._session.flush()
        return test_case

    async def save_all(self, test_cases: list[TestCase]) -> list[TestCase]:
        if not test_cases:
            return []

        self._session.add_all(test_cases)
        await self._session.flush()
        return test_cases

    async def has_embedding(self, test_case_id: int) -> bool:
        statement = text("SELECT embedding IS NOT NULL FROM test_cases WHERE id = :test_case_id")
        result = await self._session.execute(statement, {"test_case_id": test_case_id})
        return bool(result.scalar_one())

    async def set_embedding(self, test_case_id: int, embedding: list[float]) -> None:
        statement = text("UPDATE test_cases SET embedding = CAST(:embedding AS vector) WHERE id = :test_case_id")
        await self._session.execute(
            statement,
            {"test_case_id": test_case_id, "embedding": self._vector_literal(embedding)},
        )

    async def set_embeddings(self, embeddings: list[tuple[int, list[float]]]) -> None:
        if not embeddings:
            return
        statement = text("UPDATE test_cases SET embedding = CAST(:embedding AS vector) WHERE id = :test_case_id")
        parameters = [
            {"test_case_id": test_case_id, "embedding": self._vector_literal(vector)}
            for test_case_id, vector in embeddings
        ]
        await self._session.execute(statement, parameters)

    async def clear_embedding(self, test_case_id: int) -> None:
        await self._session.execute(
            text("UPDATE test_cases SET embedding = NULL WHERE id = :test_case_id"),
            {"test_case_id": test_case_id},
        )

    async def find_duplicate_candidates(
        self,
        *,
        test_case_id: int,
        module_id: int,
        owner_id: int | None,
        threshold: float,
        offset: int,
        limit: int,
    ) -> tuple[list[DuplicateCandidateRecord], int]:
        filter_owner = owner_id is not None
        parameters = {
            "test_case_id": test_case_id,
            "module_id": module_id,
            "max_distance": 1.0 - threshold,
        }
        if owner_id is not None:
            parameters["owner_id"] = owner_id

        count_result = await self._session.execute(
            self._duplicate_statement(filter_owner, count=True),
            parameters,
        )
        total = int(count_result.scalar_one())

        parameters["offset"] = offset
        parameters["limit"] = limit
        result = await self._session.execute(
            self._duplicate_statement(filter_owner),
            parameters,
        )
        candidates = [self._to_duplicate_candidate(row) for row in result.mappings().all()]
        return candidates, total

    async def get_duplicate_similarity(
        self,
        *,
        target_id: int,
        source_id: int,
    ) -> float | None:
        result = await self._session.execute(
            text(_DUPLICATE_PAIR_SIMILARITY),
            {
                "target_id": target_id,
                "source_id": source_id,
            },
        )
        similarity = result.scalar_one_or_none()
        if similarity is None:
            return None
        return max(0.0, min(1.0, float(similarity)))

    @staticmethod
    def _duplicate_statement(
        filter_owner: bool,
        *,
        count: bool = False,
    ):
        if count:
            query = _DUPLICATE_COUNT_OWNER if filter_owner else _DUPLICATE_COUNT_ALL
        else:
            query = _DUPLICATE_LIST_OWNER if filter_owner else _DUPLICATE_LIST_ALL
        return text(query)

    @staticmethod
    def _to_duplicate_candidate(row) -> DuplicateCandidateRecord:  # type: ignore[no-untyped-def]
        return DuplicateCandidateRecord(
            id=int(row["id"]),
            requirement_id=int(row["requirement_id"]),
            summary=str(row["summary"]),
            status=TestCaseStatus(row["status"]),
            priority=Priority(row["priority"]),
            similarity=max(0.0, min(1.0, float(row["similarity"]))),
        )

    @staticmethod
    def _vector_literal(embedding: list[float]) -> str:
        return "[" + ",".join(str(float(value)) for value in embedding) + "]"

    async def list_requirement_revalidation_candidates_for_update(self, requirement_id: int) -> list[TestCase]:
        statement = (
            select(TestCase)
            .where(
                TestCase.requirement_id == requirement_id,
                TestCase.status.in_({TestCaseStatus.APPROVED, TestCaseStatus.EXPORTED}),
            )
            .with_for_update()
        )
        result = await self._session.execute(statement.order_by(TestCase.id.asc()))
        return list(result.scalars().all())

    async def list_approved_for_export(
        self,
        *,
        module_id: int,
        owner_id: int | None,
    ) -> list[TestCase]:
        statement = select(TestCase).where(
            TestCase.module_id == module_id,
            TestCase.status == TestCaseStatus.APPROVED,
        )
        if owner_id is not None:
            statement = statement.where(TestCase.created_by == owner_id)
        result = await self._session.execute(statement.order_by(TestCase.id.asc()))
        return list(result.scalars().all())

    async def list_accessible(
        self,
        *,
        owner_id: int | None,
        requirement_id: int | None,
        case_status: TestCaseStatus | None,
        offset: int,
        limit: int,
    ) -> list[TestCase]:
        statement = self._apply_filters(
            select(TestCase),
            owner_id=owner_id,
            requirement_id=requirement_id,
            case_status=case_status,
        )

        # BR-09: review high-priority test cases before medium and low priority.
        priority_order = case(
            (TestCase.priority == Priority.HIGH, 0),
            (TestCase.priority == Priority.MEDIUM, 1),
            (TestCase.priority == Priority.LOW, 2),
            else_=3,
        )

        result = await self._session.execute(
            statement.order_by(priority_order.asc(), TestCase.id.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def count_accessible(
        self,
        *,
        owner_id: int | None,
        requirement_id: int | None,
        case_status: TestCaseStatus | None,
    ) -> int:
        statement = self._apply_filters(
            select(func.count()).select_from(TestCase),
            owner_id=owner_id,
            requirement_id=requirement_id,
            case_status=case_status,
        )
        result = await self._session.execute(statement)
        return int(result.scalar_one())

    @staticmethod
    def _apply_filters(
        statement,
        *,
        owner_id: int | None,
        requirement_id: int | None,
        case_status: TestCaseStatus | None,
    ):
        if owner_id is not None:
            statement = statement.where(TestCase.created_by == owner_id)
        if requirement_id is not None:
            statement = statement.where(TestCase.requirement_id == requirement_id)
        if case_status is not None:
            statement = statement.where(TestCase.status == case_status)
        return statement
