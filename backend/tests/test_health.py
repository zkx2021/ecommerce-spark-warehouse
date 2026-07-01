from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_endpoint_returns_project_status():
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "ecommerce-spark-warehouse-api"
    }
