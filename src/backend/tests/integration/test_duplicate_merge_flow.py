# Source assistance: OpenAI ChatGPT, 2026-08-28 (AI-05).

from collections.abc import Callable

from fastapi.testclient import TestClient

DatabaseQuery = Callable[[str, dict | None], list[dict]]
Headers = dict[str, str]


def create_source_data(
    client: TestClient,
    login: Callable[[str], Headers],
) -> tuple[int, int, Headers]:
    manager_headers = login("manager.integration@example.com")

    module_response = client.post(
        "/api/v1/modules",
        headers=manager_headers,
        json={"name": "Duplicate Merge", "parent_id": None},
    )
    assert module_response.status_code == 201
    module_id = module_response.json()["id"]

    qa_headers = login("qa.integration@example.com")
    requirement_response = client.post(
        "/api/v1/requirements",
        headers=qa_headers,
        json={
            "module_id": module_id,
            "content": ("Nguoi dung co the tao booking khi tat ca du lieu dau vao deu hop le."),
            "acceptance_criteria": ("He thong tao booking va luu thong tin thanh cong."),
        },
    )
    assert requirement_response.status_code == 201

    return module_id, requirement_response.json()["id"], qa_headers


def seed_duplicate_pair(
    database_write: DatabaseQuery,
    module_id: int,
    requirement_id: int,
) -> tuple[int, int]:
    embedding = "[" + ",".join(["1"] + ["0"] * 1535) + "]"

    rows = database_write(
        """
        INSERT INTO test_cases (
            requirement_id, module_id, summary, preconditions,
            steps, expected_result, priority, test_techniques,
            status, created_by, lock_version, tags, embedding
        )
        SELECT
            :requirement_id,
            :module_id,
            item.summary,
            '["Nguoi dung da dang nhap"]'::json,
            '["Nhap thong tin hop le", "Bam Dat phong"]'::json,
            'Booking duoc tao thanh cong',
            item.priority::test_case_priority,
            '["equivalence_partitioning"]'::json,
            'draft'::test_case_status,
            u.id,
            1,
            '[]'::json,
            CAST(:embedding AS vector)
        FROM users u
        CROSS JOIN (
            VALUES
                ('Tao booking voi du lieu hop le', 'low'),
                ('Tao booking khi du lieu hop le', 'high')
        ) AS item(summary, priority)
        WHERE u.email = 'qa.integration@example.com'
        RETURNING id
        """,
        {
            "requirement_id": requirement_id,
            "module_id": module_id,
            "embedding": embedding,
        },
    )

    assert len(rows) == 2
    return rows[0]["id"], rows[1]["id"]


def merge_duplicate(
    client: TestClient,
    headers: Headers,
    target_id: int,
    source_id: int,
):
    response = client.post(
        f"/api/v1/test-cases/{target_id}/merge-duplicate",
        headers=headers,
        json={
            "lock_version": 1,
            "source_test_case_id": source_id,
        },
    )
    assert response.status_code == 200
    return response


def assert_merge_records(
    database_rows: DatabaseQuery,
    target_id: int,
    source_id: int,
) -> None:
    rows = database_rows(
        """
        SELECT id, status::text AS status, lock_version,
               priority::text AS priority, review_note,
               embedding IS NULL AS embedding_cleared
        FROM test_cases
        WHERE id IN (:target_id, :source_id)
        ORDER BY id
        """,
        {
            "target_id": target_id,
            "source_id": source_id,
        },
    )
    records = {row["id"]: row for row in rows}

    assert records[target_id]["status"] == "draft"
    assert records[target_id]["priority"] == "high"
    assert records[target_id]["lock_version"] == 2
    assert records[target_id]["embedding_cleared"] is True

    assert records[source_id]["status"] == "rejected"
    assert records[source_id]["lock_version"] == 2
    assert records[source_id]["embedding_cleared"] is True


def assert_merge_history(
    database_rows: DatabaseQuery,
    target_id: int,
    source_id: int,
) -> None:
    versions = database_rows(
        """
        SELECT test_case_id, COUNT(*) AS total
        FROM test_case_versions
        WHERE test_case_id IN (:target_id, :source_id)
        GROUP BY test_case_id
        """,
        {
            "target_id": target_id,
            "source_id": source_id,
        },
    )
    assert {row["test_case_id"]: row["total"] for row in versions} == {
        target_id: 1,
        source_id: 1,
    }

    audits = database_rows(
        """
        SELECT entity_id, action::text AS action
        FROM audit_logs
        WHERE entity_type = 'test_case'
          AND entity_id IN (:target_id, :source_id)
        """,
        {
            "target_id": target_id,
            "source_id": source_id,
        },
    )
    audit_map = {(row["entity_id"], row["action"]) for row in audits}
    assert (
        target_id,
        "edit_test_case",
    ) in audit_map
    assert (
        source_id,
        "reject_test_case",
    ) in audit_map


def test_merge_duplicate_giu_target_va_reject_source(
    client: TestClient,
    login: Callable[[str], Headers],
    database_write: DatabaseQuery,
    database_rows: DatabaseQuery,
) -> None:
    module_id, requirement_id, qa_headers = create_source_data(client, login)
    target_id, source_id = seed_duplicate_pair(
        database_write,
        module_id,
        requirement_id,
    )

    response = merge_duplicate(
        client,
        qa_headers,
        target_id,
        source_id,
    )
    body = response.json()

    assert body["mergedSourceId"] == source_id
    assert body["similarity"] > 0.99
    assert body["target"]["id"] == target_id
    assert body["target"]["status"] == "draft"
    assert body["target"]["priority"] == "high"
    assert body["target"]["lock_version"] == 2

    assert_merge_records(
        database_rows,
        target_id,
        source_id,
    )


def test_merge_duplicate_tao_version_va_audit(
    client: TestClient,
    login: Callable[[str], Headers],
    database_write: DatabaseQuery,
    database_rows: DatabaseQuery,
) -> None:
    module_id, requirement_id, qa_headers = create_source_data(client, login)
    target_id, source_id = seed_duplicate_pair(
        database_write,
        module_id,
        requirement_id,
    )

    merge_duplicate(
        client,
        qa_headers,
        target_id,
        source_id,
    )
    assert_merge_history(
        database_rows,
        target_id,
        source_id,
    )
