import base64
import secrets
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPBearer
from ..config import settings

# Swagger Security Schemes
basic_security = HTTPBasic(
    scheme_name="BasicAuth",
    auto_error=False,  # Allows other authentication routes to fall through
)

bearer_security = HTTPBearer(
    scheme_name="BearerAuth",
    auto_error=False,  # Allows other authentication routes to fall through
)

logs_basic_security = HTTPBasic(
    scheme_name="LogsBasicAuth",
    realm="Request Logs Dashboard",
)


def get_logs_basic_auth(
    credentials: Optional[HTTPBasicCredentials] = Depends(logs_basic_security),
):
    """
    HTTP Basic Authentication dependency for protecting the logs dashboard and JSON endpoint.
    Triggers native browser username/password prompt if missing or invalid.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view request logs",
            headers={"WWW-Authenticate": 'Basic realm="Request Logs Dashboard"'},
        )

    valid_user = secrets.compare_digest(
        credentials.username,
        settings.VALID_BASIC_USER,
    )
    valid_pass = secrets.compare_digest(
        credentials.password,
        settings.VALID_BASIC_PASS,
    )

    if not valid_user or not valid_pass:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": 'Basic realm="Request Logs Dashboard"'},
        )

    return credentials.username



def check_basic_auth(authorization: Optional[str]):
    """
    Validate HTTP Basic Authentication.

    Returns:
        (success, authentication_type, message)
    """
    if not authorization or not authorization.startswith("Basic "):
        return (
            False,
            "NONE / INVALID",
            "Missing Basic Authentication",
        )

    try:
        encoded_credentials = authorization.split(" ", 1)[1]
        decoded_bytes = base64.b64decode(encoded_credentials)
        decoded_string = decoded_bytes.decode("utf-8")
        username, password = decoded_string.split(":", 1)

        valid_username = secrets.compare_digest(
            username,
            settings.VALID_BASIC_USER,
        )
        valid_password = secrets.compare_digest(
            password,
            settings.VALID_BASIC_PASS,
        )

        if valid_username and valid_password:
            return (
                True,
                "BASIC AUTH",
                "Authenticated via Basic Auth",
            )

        return (
            False,
            "BASIC AUTH",
            "Invalid Basic Auth credentials",
        )

    except (ValueError, UnicodeDecodeError):
        return (
            False,
            "BASIC AUTH",
            "Invalid Basic Auth format",
        )


def check_bearer_token(authorization: Optional[str]):
    """
    Validate OAuth Bearer Token.

    Returns:
        (success, authentication_type, message)
    """
    if not authorization or not authorization.startswith("Bearer "):
        return (
            False,
            "NONE / INVALID",
            "Missing Bearer Token",
        )

    token = authorization.split(" ", 1)[1]

    if secrets.compare_digest(
        token,
        settings.VALID_BEARER_TOKEN,
    ):
        return (
            True,
            "OAUTH / BEARER TOKEN",
            "Authenticated via Bearer Token",
        )

    return (
        False,
        "OAUTH / BEARER TOKEN",
        "Invalid Bearer Token",
    )


def check_api_key(
    x_api_key: Optional[str],
    api_key_header: Optional[str],
    query_api_key: Optional[str],
):
    """
    Validate API Key from headers or query parameters.

    Returns:
        (success, authentication_type, message)
    """
    # 1. X-API-Key
    if x_api_key:
        if secrets.compare_digest(x_api_key, settings.VALID_API_KEY):
            return (
                True,
                "X-API-KEY",
                "Authenticated via X-API-Key",
            )
        return (
            False,
            "X-API-KEY",
            "Invalid X-API-Key",
        )

    # 2. ApiKey header
    if api_key_header:
        if secrets.compare_digest(api_key_header, settings.VALID_API_KEY):
            return (
                True,
                "APIKEY HEADER",
                "Authenticated via ApiKey header",
            )
        return (
            False,
            "APIKEY HEADER",
            "Invalid ApiKey header",
        )

    # 3. Query parameter
    if query_api_key:
        if secrets.compare_digest(query_api_key, settings.VALID_API_KEY):
            return (
                True,
                "QUERY PARAMETER API KEY",
                "Authenticated via Query Parameter API Key",
            )
        return (
            False,
            "QUERY PARAMETER API KEY",
            "Invalid Query Parameter API Key",
        )

    return (
        False,
        "NONE / INVALID",
        "Missing API Key",
    )


def check_auth(
    authorization: Optional[str],
    x_api_key: Optional[str],
    api_key_header: Optional[str],
    query_api_key: Optional[str],
):
    """
    Validate any supported authentication method sequentially.

    Returns:
        (success, authentication_type, message)
    """
    if authorization:
        if authorization.startswith("Basic "):
            res = check_basic_auth(authorization)
            if res[0] or settings.REQUIRE_AUTH:
                return res
        elif authorization.startswith("Bearer "):
            res = check_bearer_token(authorization)
            if res[0] or settings.REQUIRE_AUTH:
                return res

    res = check_api_key(
        x_api_key=x_api_key,
        api_key_header=api_key_header,
        query_api_key=query_api_key,
    )

    if res[0]:
        return res

    if not settings.REQUIRE_AUTH:
        return (
            True,
            "ANONYMOUS / NONE",
            "Authentication bypassed (MOCK_REQUIRE_AUTH=false)",
        )

    return res

