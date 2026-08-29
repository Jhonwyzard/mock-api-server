from app.config import settings


def test_basic_auth_success(client):
    """Verify GET /basic/auth succeeds with valid credentials."""
    response = client.get(
        "/basic/auth",
        auth=(settings.VALID_BASIC_USER, settings.VALID_BASIC_PASS),
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Basic Authentication successful",
        "username": settings.VALID_BASIC_USER,
    }


def test_basic_auth_invalid(client):
    """Verify GET /basic/auth fails with invalid credentials."""
    response = client.get(
        "/basic/auth",
        auth=("baduser", "badpass"),
    )
    assert response.status_code == 401
    assert "Invalid Basic Auth" in response.json()["detail"]


def test_basic_auth_missing(client):
    """Verify GET /basic/auth fails with missing credentials."""
    response = client.get("/basic/auth")
    assert response.status_code == 401


def test_oauth_protected_success(client):
    """Verify GET /oauth/protected succeeds with a valid bearer token."""
    response = client.get(
        "/oauth/protected",
        headers={"Authorization": f"Bearer {settings.VALID_BEARER_TOKEN}"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "OAuth Bearer Token is valid",
    }


def test_oauth_protected_invalid(client):
    """Verify GET /oauth/protected fails with an invalid bearer token."""
    response = client.get(
        "/oauth/protected",
        headers={"Authorization": "Bearer badtoken"},
    )
    assert response.status_code == 401
    assert "Invalid Bearer Token" in response.json()["detail"]


def test_oauth_protected_missing(client):
    """Verify GET /oauth/protected fails with missing bearer token."""
    response = client.get("/oauth/protected")
    assert response.status_code == 401
