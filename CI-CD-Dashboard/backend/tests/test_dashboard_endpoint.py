from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dashboard_endpoint_returns_summary() -> None:
    """The dashboard endpoint should return a summary payload even with an empty database."""
    response = client.get("/api/dashboard")

    assert response.status_code == 200
    assert "total_builds" in response.json()
    assert "success_rate" in response.json()
    assert "failure_rate" in response.json()
