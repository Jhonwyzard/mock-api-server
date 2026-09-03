from app.config import settings
from app.core.rate_limiter import rate_limiter


def test_rate_limiting(client, monkeypatch):
    """Verify that requests exceeding RATE_LIMIT_PER_SEC trigger HTTP 429 Too Many Requests."""
    rate_limiter.reset()
    monkeypatch.setattr(settings, "ENABLE_RATE_LIMIT", True)
    monkeypatch.setattr(settings, "RATE_LIMIT_PER_SEC", 3)

    # First 3 requests succeed (200 OK)
    for _ in range(3):
        res = client.get("/")
        assert res.status_code == 200

    # 4th request exceeds rate limit (429 Too Many Requests)
    res_exceeded = client.get("/")
    assert res_exceeded.status_code == 429
    assert res_exceeded.json()["status"] == "error"
    assert "Rate limit exceeded" in res_exceeded.json()["message"]

    # Reset rate limiter for subsequent tests
    rate_limiter.reset()
