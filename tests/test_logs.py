from app.config import settings
from app.core.logger import log_store


auth_headers = {"Authorization": "Basic YWRtaW46c2VjcmV0cGFzc3dvcmQ="}  # admin:secretpassword


def test_logs_unauthenticated_browser_redirects(client, monkeypatch):
    """Verify /logs redirects browser navigation (text/html) to /logs/login when REQUIRE_LOGS_AUTH is True."""
    monkeypatch.setattr(settings, "REQUIRE_LOGS_AUTH", True)
    res_html = client.get("/logs", headers={"Accept": "text/html"}, follow_redirects=False)
    assert res_html.status_code == 303
    assert res_html.headers["location"] == "/logs/login"


def test_logs_unauthenticated_api_returns_401(client, monkeypatch):
    """Verify /logs/json returns 401 Unauthorized when unauthenticated and REQUIRE_LOGS_AUTH is True."""
    monkeypatch.setattr(settings, "REQUIRE_LOGS_AUTH", True)
    res_json = client.get("/logs/json")
    assert res_json.status_code == 401
    assert "WWW-Authenticate" in res_json.headers



def test_logs_login_page_renders(client):
    """Verify GET /logs/login renders login HTML page."""
    response = client.get("/logs/login")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Sign In to Dashboard" in response.text


def test_logs_login_flow(client, monkeypatch):
    """Verify POST /logs/login authenticates and allows access via cookie session."""
    monkeypatch.setattr(settings, "REQUIRE_LOGS_AUTH", True)
    # Invalid login

    res_invalid = client.post("/logs/login", data={"username": "admin", "password": "wrong"})
    assert res_invalid.status_code == 401

    # Valid login
    res_valid = client.post(
        "/logs/login",
        data={"username": settings.LOGS_BASIC_USER, "password": settings.LOGS_BASIC_PASS},
    )
    assert res_valid.status_code == 200
    assert "logs_session" in res_valid.cookies

    # Access /logs and /logs/json with cookie
    res_dashboard = client.get("/logs", cookies=res_valid.cookies)
    assert res_dashboard.status_code == 200
    assert "API Mock Server" in res_dashboard.text

    res_json = client.get("/logs/json", cookies=res_valid.cookies)
    assert res_json.status_code == 200

    # Logout
    res_logout = client.post("/logs/logout", cookies=res_valid.cookies)
    assert res_logout.status_code == 200


def test_logs_dashboard_html_basic_auth_header(client):
    """Verify GET /logs renders the dashboard HTML successfully with Basic Auth header."""
    response = client.get("/logs", headers=auth_headers)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "API Mock Server" in response.text


def test_logs_json_initial(client):
    """Verify GET /logs/json returns an empty log array initially with Basic Auth."""
    response = client.get("/logs/json", headers=auth_headers)
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

    response = client.get("/logs/json", headers=auth_headers)
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
    response = client.delete("/logs", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Request logs cleared",
    }

    # Confirm empty store
    assert log_store.count() == 0

    json_response = client.get("/logs/json", headers=auth_headers)
    assert json_response.json()["count"] == 0


def test_logs_require_logs_auth_bypassed(client, monkeypatch):
    """Verify /logs and /logs/json allow unauthenticated access when REQUIRE_LOGS_AUTH is False."""
    monkeypatch.setattr(settings, "REQUIRE_LOGS_AUTH", False)

    res_html = client.get("/logs")
    assert res_html.status_code == 200

    res_json = client.get("/logs/json")
    assert res_json.status_code == 200
    assert "count" in res_json.json()



