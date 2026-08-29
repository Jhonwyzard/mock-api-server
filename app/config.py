import os

class Settings:
    """Application settings, reading from environment variables with safe defaults."""
    
    # Basic Authentication
    VALID_BASIC_USER: str = os.getenv("MOCK_BASIC_USER", "admin")
    VALID_BASIC_PASS: str = os.getenv("MOCK_BASIC_PASS", "secretpassword")

    # API Key
    VALID_API_KEY: str = os.getenv("MOCK_API_KEY", "my-super-secret-api-key-123")

    # OAuth / Bearer Token
    VALID_BEARER_TOKEN: str = os.getenv("MOCK_BEARER_TOKEN", "oauth-token-xyz-789")

    # Log store configuration
    MAX_LOGS: int = int(os.getenv("MOCK_MAX_LOGS", "100"))

settings = Settings()
