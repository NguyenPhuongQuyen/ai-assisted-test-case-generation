# Source assistance: OpenAI ChatGPT, 2026-08-28 (AI-05).

from collections.abc import Callable

import pytest
from app.common.task_queue import GenerationTaskQueue
from fastapi.testclient import TestClient

Headers = dict[str, str]
DatabaseQuery = Callable[
    [str, dict | None],
    list[dict],
]


def create_generation_requirement(
    client: TestClient,
    login: Callable[[str], Headers],
) -> tuple[Headers, int]:
    manager_headers = login("manager.integration@example.com")
    module_response = client.post(
        "/api/v1/modules",
        headers=manager_headers,
        json={
            "name": "Generation Integration",
            "parent_id": None,
        },
    )
    assert module_response.status_code == 201

    qa_headers = login("qa.integration@example.com")
    response = client.post(
        "/api/v1/requirements",
        headers=qa_headers,
        json={
            "module_id": module_response.json()["id"],
            "content": ("Nguoi dung dat phong khi thong tin bat buoc deu hop le."),
            "acceptance_criteria": ("He thong tao cac test case o trang thai DRAFT de QA tiep tuc review."),
        },
    )
    assert response.status_code == 201
    return qa_headers, response.json()["id"]


def capture_enqueued_jobs(
    monkeypatch: pytest.MonkeyPatch,
) -> list[int]:
    enqueued: list[int] = []

    def fake_enqueue(
        _queue: GenerationTaskQueue,
        job_id: int,
    ) -> None:
        enqueued.append(job_id)

    monkeypatch.setattr(
        GenerationTaskQueue,
        "enqueue",
        fake_enqueue,
    )
    return enqueued


def assert_job_in_database(
    database_rows: DatabaseQuery,
    job_id: int,
    requirement_id: int,
) -> None:
    rows = database_rows(
        """
        SELECT
            requirement_id,
            status::text AS status,
            error_code
        FROM generation_jobs
        WHERE id = :job_id
        """,
        {"job_id": job_id},
    )
    assert len(rows) == 1
    assert rows[0]["requirement_id"] == requirement_id
    assert rows[0]["status"] == "queued"
    assert rows[0]["error_code"] is None


def test_submit_generation_tao_queued_job_qua_api(
    client: TestClient,
    login: Callable[[str], Headers],
    database_rows: DatabaseQuery,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    enqueued = capture_enqueued_jobs(monkeypatch)
    headers, requirement_id = create_generation_requirement(client, login)

    response = client.post(
        f"/api/v1/requirements/{requirement_id}/test-cases",
        headers=headers,
    )
    assert response.status_code == 202

    body = response.json()
    assert body["requirement_id"] == requirement_id
    assert body["status"] == "queued"
    assert body["error_code"] is None
    assert enqueued == [body["id"]]

    assert_job_in_database(
        database_rows,
        body["id"],
        requirement_id,
    )

    status_response = client.get(
        f"/api/v1/generation-jobs/{body['id']}",
        headers=headers,
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "queued"
