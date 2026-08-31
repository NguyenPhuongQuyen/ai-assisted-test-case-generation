from fastapi.testclient import TestClient

from .conftest import TEST_PASSWORD


def test_dang_nhap_hop_le_tra_ve_jwt(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "qa.integration@example.com",
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "qa.integration@example.com"
    assert body["user"]["role"] == "qa"


def test_dang_nhap_sai_mat_khau_bi_tu_choi(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "qa.integration@example.com",
            "password": "Sai_Mat_Khau_123!",
        },
    )

    assert response.status_code == 401
