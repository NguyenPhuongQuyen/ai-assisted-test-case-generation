# Source assistance: OpenAI ChatGPT, 2026-08-28 (AI-05).

from collections.abc import Callable

from fastapi.testclient import TestClient

DatabaseQuery = Callable[
    [str, dict | None],
    list[dict],
]


def create_br08_requirement(
    client: TestClient,
    login: Callable[[str], dict[str, str]],
) -> tuple[dict[str, str], dict, int]:
    manager_headers = login("manager.integration@example.com")
    module_response = client.post(
        "/api/v1/modules",
        headers=manager_headers,
        json={
            "name": "BR08 Booking",
            "parent_id": None,
        },
    )
    assert module_response.status_code == 201
    module_id = module_response.json()["id"]

    qa_headers = login("qa.integration@example.com")
    response = client.post(
        "/api/v1/requirements",
        headers=qa_headers,
        json={
            "module_id": module_id,
            "content": ("Nguoi dung co the dat phong khi tat ca thong tin bat buoc hop le."),
            "acceptance_criteria": ("He thong tao booking thanh cong va luu du lieu."),
        },
    )
    assert response.status_code == 201
    return qa_headers, response.json(), module_id


def seed_br08_approved_case(
    database_write: DatabaseQuery,
    requirement_id: int,
    module_id: int,
) -> int:
    rows = database_write(
        """
        INSERT INTO test_cases (
            requirement_id, module_id, summary,
            preconditions, steps, expected_result,
            priority, test_techniques, review_note,
            status, created_by, lock_version, tags
        )
        SELECT
            :requirement_id,
            :module_id,
            'Dat phong voi du lieu hop le',
            '["Nguoi dung da dang nhap"]'::json,
            '["Mo man hinh dat phong", "Nhap du lieu hop le", "Bam Dat phong"]'::json,
            'Booking duoc tao thanh cong',
            'high'::test_case_priority,
            '["equivalence_partitioning"]'::json,
            'Da duyet',
            'approved'::test_case_status,
            u.id,
            1,
            '[]'::json
        FROM users u
        WHERE u.email = 'qa.integration@example.com'
        RETURNING id
        """,
        {
            "requirement_id": requirement_id,
            "module_id": module_id,
        },
    )
    assert len(rows) == 1
    return rows[0]["id"]


def assert_br08_evidence(
    database_rows: DatabaseQuery,
    test_case_id: int,
    requirement_id: int,
) -> None:
    cases = database_rows(
        """
        SELECT status::text AS status, lock_version
        FROM test_cases
        WHERE id = :test_case_id
        """,
        {"test_case_id": test_case_id},
    )
    assert len(cases) == 1
    assert cases[0]["status"] == "needs_fix"
    assert cases[0]["lock_version"] == 2

    versions = database_rows(
        """
        SELECT COUNT(*) AS total
        FROM test_case_versions
        WHERE test_case_id = :test_case_id
        """,
        {"test_case_id": test_case_id},
    )
    assert versions[0]["total"] == 1

    audits = database_rows(
        """
        SELECT COUNT(*) AS total
        FROM audit_logs
        WHERE entity_type = 'requirement'
          AND entity_id = :requirement_id
          AND action::text = 'update_requirement'
        """,
        {"requirement_id": requirement_id},
    )
    assert audits[0]["total"] == 1


def test_sua_requirement_chuyen_approved_test_case_sang_needs_fix(
    client: TestClient,
    login: Callable[[str], dict[str, str]],
    database_write: DatabaseQuery,
    database_rows: DatabaseQuery,
) -> None:
    qa_headers, requirement, module_id = create_br08_requirement(client, login)
    requirement_id = requirement["id"]
    test_case_id = seed_br08_approved_case(
        database_write,
        requirement_id,
        module_id,
    )

    response = client.patch(
        f"/api/v1/requirements/{requirement_id}",
        headers=qa_headers,
        json={
            "lock_version": requirement["lock_version"],
            "content": ("Nguoi dung co the dat phong khi du lieu hop le va phong van con trong."),
        },
    )

    assert response.status_code == 200
    assert response.json()["lock_version"] == 2
    assert_br08_evidence(
        database_rows,
        test_case_id,
        requirement_id,
    )
