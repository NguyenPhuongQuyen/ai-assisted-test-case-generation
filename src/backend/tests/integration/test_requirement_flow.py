from collections.abc import Callable

from fastapi.testclient import TestClient

DatabaseQuery = Callable[
    [str, dict | None],
    list[dict],
]


def test_manager_tao_module_va_qa_tao_requirement(
    client: TestClient,
    login: Callable[[str], dict[str, str]],
    database_rows: DatabaseQuery,
) -> None:
    manager_headers = login("manager.integration@example.com")

    module_response = client.post(
        "/api/v1/modules",
        headers=manager_headers,
        json={
            "name": "Integration Booking",
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
            "content": ("Nguoi dung co the tao booking khi thong tin bat buoc deu hop le."),
            "acceptance_criteria": ("He thong luu requirement va lien ket dung module."),
        },
    )

    assert requirement_response.status_code == 201

    body = requirement_response.json()
    requirement_id = body["id"]

    assert body["module_id"] == module_id
    assert body["lock_version"] == 1

    rows = database_rows(
        """
        SELECT
            r.module_id,
            r.content,
            u.email AS creator_email
        FROM requirements r
        JOIN users u ON u.id = r.created_by
        WHERE r.id = :requirement_id
        """,
        {"requirement_id": requirement_id},
    )

    assert len(rows) == 1
    assert rows[0]["module_id"] == module_id
    assert rows[0]["creator_email"] == "qa.integration@example.com"

    audit_rows = database_rows(
        """
        SELECT id
        FROM audit_logs
        WHERE entity_type = 'requirement'
          AND entity_id = :requirement_id
        """,
        {"requirement_id": requirement_id},
    )

    assert len(audit_rows) == 1


def test_qa_khong_duoc_tao_module(
    client: TestClient,
    login: Callable[[str], dict[str, str]],
) -> None:
    qa_headers = login("qa.integration@example.com")

    response = client.post(
        "/api/v1/modules",
        headers=qa_headers,
        json={
            "name": "Module QA khong duoc tao",
            "parent_id": None,
        },
    )

    assert response.status_code == 403
