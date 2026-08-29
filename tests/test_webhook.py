import base64
from app.config import settings
from app.core.logger import log_store


def test_webhook_basic_auth_success(client):
    """Verify /webhook accepts valid Basic Auth credentials."""
    credentials = f"{settings.VALID_BASIC_USER}:{settings.VALID_BASIC_PASS}"
    encoded = base64.b64encode(credentials.encode()).decode()
    
    payload = {"event": "test-basic", "id": "123"}
    response = client.post(
        "/webhook",
        headers={"Authorization": f"Basic {encoded}"},
        json=payload,
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["authentication_type"] == "BASIC AUTH"
    
    # Check that it logged correctly
    assert log_store.count() == 1
    logged_request = log_store.get_all()[0]
    assert logged_request["authentication_type"] == "BASIC AUTH"
    assert logged_request["authentication_success"] is True
    assert logged_request["body"] == payload


def test_webhook_bearer_token_success(client):
    """Verify /webhook accepts a valid OAuth Bearer token."""
    payload = {"event": "test-bearer", "id": "456"}
    response = client.post(
        "/webhook",
        headers={"Authorization": f"Bearer {settings.VALID_BEARER_TOKEN}"},
        json=payload,
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["authentication_type"] == "OAUTH / BEARER TOKEN"
    
    assert log_store.count() == 1
    logged_request = log_store.get_all()[0]
    assert logged_request["authentication_type"] == "OAUTH / BEARER TOKEN"
    assert logged_request["body"] == payload


def test_webhook_x_api_key_success(client):
    """Verify /webhook accepts a valid X-API-Key header."""
    payload = {"event": "test-x-api-key", "id": "789"}
    response = client.post(
        "/webhook",
        headers={"X-API-Key": settings.VALID_API_KEY},
        json=payload,
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["authentication_type"] == "X-API-KEY"
    
    assert log_store.count() == 1
    logged_request = log_store.get_all()[0]
    assert logged_request["authentication_type"] == "X-API-KEY"


def test_webhook_api_key_header_success(client):
    """Verify /webhook accepts a valid ApiKey header."""
    payload = {"event": "test-api-key-header", "id": "101"}
    response = client.post(
        "/webhook",
        headers={"ApiKey": settings.VALID_API_KEY},
        json=payload,
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["authentication_type"] == "APIKEY HEADER"
    
    assert log_store.count() == 1


def test_webhook_query_param_success(client):
    """Verify /webhook accepts a valid api_key query parameter."""
    payload = {"event": "test-query-param", "id": "202"}
    response = client.post(
        f"/webhook?api_key={settings.VALID_API_KEY}",
        json=payload,
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["authentication_type"] == "QUERY PARAMETER API KEY"


def test_webhook_unauthorized(client):
    """Verify /webhook rejects requests with missing or invalid auth."""
    payload = {"event": "unauthorized"}
    response = client.post("/webhook", json=payload)
    
    assert response.status_code == 401
    assert response.json()["status"] == "error"
    assert response.json()["authentication_type"] == "NONE / INVALID"
    
    # Check that failed requests are still logged!
    assert log_store.count() == 1
    logged_request = log_store.get_all()[0]
    assert logged_request["authentication_success"] is False
    assert logged_request["status_code"] == 401


def test_webhook_non_json_body(client):
    """Verify /webhook parses non-JSON bodies as plain text."""
    raw_data = "plain text webhook data"
    response = client.post(
        f"/webhook?api_key={settings.VALID_API_KEY}",
        content=raw_data,
        headers={"Content-Type": "text/plain"},
    )
    
    assert response.status_code == 200
    assert log_store.count() == 1
    logged_request = log_store.get_all()[0]
    assert logged_request["body"] == raw_data


def test_webhook_wildcard_subpath(client):
    """Verify /webhook/{path:path} receives, authenticates, and logs correctly."""
    subpath = "devices/ID/ID0001"
    payload = {"event": "wildcard-test"}
    response = client.post(
        f"/webhook/{subpath}?api_key={settings.VALID_API_KEY}",
        json=payload,
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    assert log_store.count() == 1
    logged_request = log_store.get_all()[0]
    assert logged_request["path"] == f"/webhook/{subpath}"
    assert logged_request["body"] == payload

