from fastapi.testclient import TestClient

from app.main import app


def test_health():
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_metrics():
    response = TestClient(app).get("/metrics")

    assert response.status_code == 200
    assert "send_attempts" in response.json()