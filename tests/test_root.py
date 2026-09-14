from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_returns_success() -> None:
    response = client.get("/")

    assert response.status_code == 200


def test_root_returns_expected_service_information() -> None:
    response = client.get("/")

    body = response.json()

    assert body["service"] == "Prayer Timing API"
    assert body["version"] == "0.1.0"
    assert body["status"] == "running"
