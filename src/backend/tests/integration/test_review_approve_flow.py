# Source assistance: OpenAI ChatGPT, 2026-08-28 (AI-05).

from collections.abc import Callable

from fastapi.testclient import TestClient

DatabaseQuery = Callable[[str, dict | None], list[dict]]
Headers = dict[str, str]


def create_requirement(
    client: TestClient,
    login: Callable[[str], Headers],
) -> tuple[int, int, Headers, Headers]:
    manager_headers = login("manager.integration@example.com")
    module_response = client.post(
        "/api/v1/modules",
        headers=manager_headers,
        json={"name": "Review Flow", "parent_id": None},
    )
    assert module_response.status_code == 201
    module_id = module_response.json()["id"]

    qa_headers = login("qa.integration@example.com")
    requirement_response = client.post(
        "/api/v1/requirements",
        headers=qa_headers,
        json={
            "module_id": module_id,
            "content": ("Nguoi dung co the tao don dat phong khi thong tin dau vao hop le."),
            "acceptance_criteria": ("He thong luu don dat phong va tra ve ket qua thanh cong."),
        },
    )
    assert requirement_response.status_code == 201

    return (
        module_id,
        requirement_response.json()["id"],
        qa_headers,
        manager_headers,
    )


def seed_draft_test_case(
    database_write: DatabaseQuery,
    module_id: int,
    requirement_id: int,
) -> int:
    rows = database_write(
        """
        INSERT INTO test_cases (
            requirement_id, module_id, summary, preconditions,
            steps, expected_result, priority, test_techniques,
            status, created_by, lock_version, tags
        )
        SELECT
            :requirement_id, :module_id, 'Tao booking hop le',
            '["Nguoi dung da dang nhap"]'::json,
            '["Nhap thong tin hop le", "Bam Dat phong"]'::json,
            'Booking duoc tao thanh cong',
            'high'::test_case_priority,
            '["equivalence_partitioning"]'::json,
            'draft'::test_case_status,
            u.id, 1, '[]'::json
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


def submit_and_approve(
    client: TestClient,
    test_case_id: int,
    qa_headers: Headers,
    manager_headers: Headers,
) -> None:
    review_response = client.post(
        f"/api/v1/test-cases/{test_case_id}/review",
        headers=qa_headers,
        json={"lock_version": 1},
    )
    assert review_response.status_code == 200
    assert review_response.json()["status"] == "in_review"
    assert review_response.json()["lock_version"] == 2

    approve_response = client.post(
        f"/api/v1/test-cases/{test_case_id}/approve",
        headers=manager_headers,
        json={
            "lock_version": 2,
            "review_note": "Da kiem tra va dong y.",
        },
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"
    assert approve_response.json()["lock_version"] == 3


def assert_review_history(
    database_rows: DatabaseQuery,
    test_case_id: int,
) -> None:
    versions = database_rows(
        """
        SELECT COUNT(*) AS total
        FROM test_case_versions
        WHERE test_case_id = :test_case_id
        """,
        {"test_case_id": test_case_id},
    )
    assert versions[0]["total"] == 2

    audits = database_rows(
        """
        SELECT action::text AS action
        FROM audit_logs
        WHERE entity_id = :test_case_id
          AND action::text IN (
              'submit_test_case_review',
              'approve_test_case'
          )
        """,
        {"test_case_id": test_case_id},
    )
    assert {row["action"] for row in audits} == {
        "submit_test_case_review",
        "approve_test_case",
    }


def test_qa_submit_review_va_manager_approve(
    client: TestClient,
    login: Callable[[str], Headers],
    database_write: DatabaseQuery,
    database_rows: DatabaseQuery,
) -> None:
    (
        module_id,
        requirement_id,
        qa_headers,
        manager_headers,
    ) = create_requirement(client, login)

    test_case_id = seed_draft_test_case(
        database_write,
        module_id,
        requirement_id,
    )

    submit_and_approve(
        client,
        test_case_id,
        qa_headers,
        manager_headers,
    )
    assert_review_history(
        database_rows,
        test_case_id,
    )


def test_draft_khong_duoc_approve_truc_tiep(
    client: TestClient,
    login: Callable[[str], Headers],
    database_write: DatabaseQuery,
    database_rows: DatabaseQuery,
) -> None:
    module_id, requirement_id, _, manager_headers = create_requirement(client, login)
    test_case_id = seed_draft_test_case(
        database_write,
        module_id,
        requirement_id,
    )

    response = client.post(
        f"/api/v1/test-cases/{test_case_id}/approve",
        headers=manager_headers,
        json={"lock_version": 1},
    )

    assert response.status_code == 409

    rows = database_rows(
        """
        SELECT status::text AS status, lock_version
        FROM test_cases
        WHERE id = :test_case_id
        """,
        {"test_case_id": test_case_id},
    )

    assert rows[0]["status"] == "draft"
    assert rows[0]["lock_version"] == 1


def create_approved_case(
    client: TestClient,
    login: Callable[[str], Headers],
    database_write: DatabaseQuery,
) -> tuple[int, Headers]:
    (
        module_id,
        requirement_id,
        qa_headers,
        manager_headers,
    ) = create_requirement(client, login)

    test_case_id = seed_draft_test_case(
        database_write,
        module_id,
        requirement_id,
    )
    submit_and_approve(
        client,
        test_case_id,
        qa_headers,
        manager_headers,
    )
    return test_case_id, qa_headers


def test_manager_cap_nhat_tags_va_xem_coverage_qua_api(
    client: TestClient,
    login: Callable[[str], Headers],
    database_write: DatabaseQuery,
) -> None:
    (
        module_id,
        requirement_id,
        _,
        manager_headers,
    ) = create_requirement(client, login)

    test_case_id = seed_draft_test_case(
        database_write,
        module_id,
        requirement_id,
    )

    tag_response = client.patch(
        f"/api/v1/modules/{module_id}/test-cases/{test_case_id}/tags",
        headers=manager_headers,
        json={
            "tags": [
                "Boundary",
                "boundary",
                "Payment",
            ]
        },
    )

    assert tag_response.status_code == 200
    assert tag_response.json()["tags"] == [
        "boundary",
        "payment",
    ]

    coverage_response = client.get(
        f"/api/v1/modules/{module_id}/coverage",
        headers=manager_headers,
    )

    assert coverage_response.status_code == 200
    coverage = coverage_response.json()
    assert coverage["moduleId"] == module_id
    assert coverage["totalRequirements"] == 1
    assert coverage["totalTestCases"] == 1


def test_version_list_compare_restore_qua_api(
    client: TestClient,
    login: Callable[[str], Headers],
    database_write: DatabaseQuery,
) -> None:
    test_case_id, qa_headers = create_approved_case(
        client,
        login,
        database_write,
    )

    history_response = client.get(
        f"/api/v1/test-cases/{test_case_id}/versions",
        headers=qa_headers,
    )
    assert history_response.status_code == 200

    history = history_response.json()
    assert history["total"] == 2
    assert sorted(item["versionNumber"] for item in history["data"]) == [1, 2]

    compare_response = client.get(
        f"/api/v1/test-cases/{test_case_id}/versions/compare",
        headers=qa_headers,
        params={
            "fromVersion": 1,
            "toVersion": 2,
        },
    )
    assert compare_response.status_code == 200

    comparison = compare_response.json()
    assert comparison["fromVersion"] == 1
    assert comparison["toVersion"] == 2
    assert comparison["changes"]

    restore_response = client.post(
        f"/api/v1/test-cases/{test_case_id}/versions/1/restore",
        headers=qa_headers,
        json={"lock_version": 3},
    )
    assert restore_response.status_code == 200

    restored = restore_response.json()
    assert restored["status"] == "needs_fix"
    assert restored["lock_version"] == 4
