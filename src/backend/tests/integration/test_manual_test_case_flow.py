from collections.abc import Callable

from fastapi.testclient import TestClient

DatabaseQuery = Callable[[str, dict | None], list[dict]]
Headers = dict[str, str]


def test_qa_tao_test_case_thu_cong_khong_can_ai(
    client: TestClient,
    login: Callable[[str], Headers],
    database_rows: DatabaseQuery,
) -> None:
    manager_headers = login("manager.integration@example.com")

    module_response = client.post(
        "/api/v1/modules",
        headers=manager_headers,
        json={
            "name": "Manual Test Case Integration",
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
            "content": ("Nguoi dung co the dat phong khi thong tin bat buoc hop le."),
            "acceptance_criteria": ("He thong tao booking thanh cong khi du lieu hop le."),
        },
    )

    assert requirement_response.status_code == 201
    requirement_id = requirement_response.json()["id"]

    response = client.post(
        f"/api/v1/requirements/{requirement_id}/test-cases/manual",
        headers=qa_headers,
        json={
            "summary": "Dat phong thu cong thanh cong",
            "preconditions": [
                "Nguoi dung da dang nhap",
                "Phong con trong",
            ],
            "steps": [
                "Chon phong",
                "Nhap ngay nhan va tra phong",
                "Xac nhan dat phong",
            ],
            "expected_result": "Booking duoc tao thanh cong.",
            "priority": "high",
            "test_techniques": [
                "Happy Path",
                "Equivalence Partitioning",
            ],
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["requirement_id"] == requirement_id
    assert body["module_id"] == module_id
    assert body["status"] == "draft"
    assert body["summary"] == "Dat phong thu cong thanh cong"
    assert body["priority"] == "high"
    assert body["lock_version"] == 1
    assert body["preconditions"] == [
        "Nguoi dung da dang nhap",
        "Phong con trong",
    ]
    assert body["test_techniques"] == [
        "Happy Path",
        "Equivalence Partitioning",
    ]

    versions = database_rows(
        """
        SELECT version_number
        FROM test_case_versions
        WHERE test_case_id = :test_case_id
        """,
        {"test_case_id": body["id"]},
    )

    assert versions == [{"version_number": 1}]

    generation_jobs = database_rows(
        """
        SELECT COUNT(*) AS total
        FROM generation_jobs
        WHERE requirement_id = :requirement_id
        """,
        {"requirement_id": requirement_id},
    )

    assert generation_jobs[0]["total"] == 0
