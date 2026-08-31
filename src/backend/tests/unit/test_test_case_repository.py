from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.testcases.repository import TestCaseRepository as Repository
from sqlalchemy.dialects import postgresql


@pytest.mark.asyncio
async def test_review_list_orders_high_medium_low_with_stable_secondary_order() -> None:
    scalar_result = SimpleNamespace(all=lambda: [])
    execute_result = SimpleNamespace(scalars=lambda: scalar_result)
    session = SimpleNamespace(execute=AsyncMock(return_value=execute_result))
    repository = Repository(session)

    await repository.list_accessible(
        owner_id=None,
        requirement_id=None,
        case_status=None,
        offset=0,
        limit=20,
    )

    statement = session.execute.await_args.args[0]
    sql = str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )
    normalized = " ".join(sql.lower().split())
    order_clause = normalized.split(" order by ", 1)[1]

    assert "case" in order_clause
    assert order_clause.index("'high'") < order_clause.index("'medium'") < order_clause.index("'low'")
    assert "test_cases.id desc" in order_clause
