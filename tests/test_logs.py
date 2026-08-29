from app.config import settings
from app.core.logger import log_store


def test_logs_dashboard_html(client):
    """Verify GET /logs renders the dashboard HTML successfully."""
    response = client.get("/logs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "API Mock Server" in response.text


def test_logs_json_initial(client):
    """Verify GET /logs/json returns an empty log array initially."""
    response = client.get("/logs/json")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["logs"] == []


def test_logs_json_with_records(client):
    """Verify GET /logs/json lists received webhook requests."""
    # Add a webhook request
    client.post(
        f"/webhook?api_key={settings.VALID_API_KEY}",
        json={"event": "logged-event", "id": "1"},
    )
    
    response = client.get("/logs/json")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["logs"][0]["body"]["event"] == "logged-event"


def test_clear_logs(client):
    """Verify DELETE /logs purges the logs successfully."""
    # Add a log
    client.post(
        f"/webhook?api_key={settings.VALID_API_KEY}",
        json={"event": "logged-event"},
    )
    assert log_store.count() == 1
    
    # Send clear request
    response = client.delete("/logs")
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Request logs cleared",
    }
    
    # Confirm empty store
    assert log_store.count() == 0
    
    json_response = client.get("/logs/json")
    assert json_response.json()["count"] == 0
