from collections.abc import Callable

from fastapi.testclient import TestClient

DatabaseQuery = Callable[
    [str, dict | None],
    list[dict],
]


def test_sua_requirement_chuyen_approved_test_case_sang_needs_fix(
    client: TestClient,
    login: Callable[[str], dict[str, str]],
    database_write: DatabaseQuery,
    database_rows: DatabaseQuery,
) -> None:
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

    requirement_response = client.post(
        "/api/v1/requirements",
        headers=qa_headers,
        json={
            "module_id": module_id,
            "content": ("Nguoi dung co the dat phong khi tat ca thong tin bat buoc hop le."),
            "acceptance_criteria": ("He thong tao booking thanh cong va luu du lieu."),
        },
    )

    assert requirement_response.status_code == 201

    requirement = requirement_response.json()
    requirement_id = requirement["id"]

    inserted = database_write(
        """
        INSERT INTO test_cases (
            requirement_id,
            module_id,
            summary,
            preconditions,
            steps,
            expected_result,
            priority,
            test_techniques,
            review_note,
            status,
            created_by,
            lock_version,
            tags
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

    assert len(inserted) == 1
    test_case_id = inserted[0]["id"]

    update_response = client.patch(
        f"/api/v1/requirements/{requirement_id}",
        headers=qa_headers,
        json={
            "lock_version": requirement["lock_version"],
            "content": ("Nguoi dung co the dat phong khi du lieu hop le va phong van con trong."),
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["lock_version"] == 2

    case_rows = database_rows(
        """
        SELECT
            status::text AS status,
            lock_version
        FROM test_cases
        WHERE id = :test_case_id
        """,
        {"test_case_id": test_case_id},
    )

    assert len(case_rows) == 1
    assert case_rows[0]["status"] == "needs_fix"
    assert case_rows[0]["lock_version"] == 2

    version_rows = database_rows(
        """
        SELECT COUNT(*) AS total
        FROM test_case_versions
        WHERE test_case_id = :test_case_id
        """,
        {"test_case_id": test_case_id},
    )

    assert version_rows[0]["total"] == 1

    audit_rows = database_rows(
        """
        SELECT COUNT(*) AS total
        FROM audit_logs
        WHERE entity_type = 'requirement'
          AND entity_id = :requirement_id
          AND action::text = 'update_requirement'
        """,
        {"requirement_id": requirement_id},
    )

    assert audit_rows[0]["total"] == 1
