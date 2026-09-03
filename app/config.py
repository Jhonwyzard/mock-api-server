import os

class Settings:
    """Application settings, reading from environment variables with safe defaults."""

    # Basic Authentication (for /basic/auth and /webhook)
    VALID_BASIC_USER: str = os.getenv("MOCK_BASIC_USER", "admin")
    VALID_BASIC_PASS: str = os.getenv("MOCK_BASIC_PASS", "secretpassword")

    # API Key (for /webhook)
    VALID_API_KEY: str = os.getenv("MOCK_API_KEY", "my-super-secret-api-key-123")

    # OAuth / Bearer Token (for /oauth/protected and /webhook)
    VALID_BEARER_TOKEN: str = os.getenv("MOCK_BEARER_TOKEN", "oauth-token-xyz-789")

    # Webhook authentication requirement toggle (MOCK_REQUIRE_AUTH=false allows anonymous webhooks)
    REQUIRE_AUTH: bool = os.getenv("MOCK_REQUIRE_AUTH", "true").lower() in ("true", "1", "yes")

    # Logs Dashboard Authentication toggle & credentials
    REQUIRE_LOGS_AUTH: bool = os.getenv("MOCK_REQUIRE_LOGS_AUTH", "true").lower() in ("true", "1", "yes")
    LOGS_BASIC_USER: str = os.getenv("MOCK_LOGS_USER", os.getenv("MOCK_BASIC_USER", "admin"))
    LOGS_BASIC_PASS: str = os.getenv("MOCK_LOGS_PASS", os.getenv("MOCK_BASIC_PASS", "secretpassword"))

    # Log store maximum history limit
    MAX_LOGS: int = int(os.getenv("MOCK_MAX_LOGS", "100"))

    # CORS Allow Origins
    CORS_ALLOW_ORIGINS: list = [
        origin.strip()
        for origin in os.getenv("MOCK_CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ]


settings = Settings()


