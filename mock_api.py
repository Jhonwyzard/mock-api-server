import base64
import html
import json
import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Request,
)
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBasic,
    HTTPBasicCredentials,
    HTTPBearer,
)

app = FastAPI(
    title="API Mock Server",
    description="Generic API mock server for authentication and webhook testing",
    version="1.0.0",
)


# =============================================================================
# Test Configuration
# =============================================================================

# Basic Authentication
VALID_BASIC_USER = "admin"
VALID_BASIC_PASS = "secretpassword"

# API Key
VALID_API_KEY = "my-super-secret-api-key-123"

# OAuth / Bearer Token
VALID_BEARER_TOKEN = "oauth-token-xyz-789"


# =============================================================================
# Swagger Security Schemes
# =============================================================================

basic_security = HTTPBasic(
    scheme_name="BasicAuth",
)

bearer_security = HTTPBearer(
    scheme_name="BearerAuth",
)


# =============================================================================
# Request Logs
# =============================================================================

# In-memory request history.
#
# This is intentionally simple for a test/mock server.
# Logs are lost when the application restarts.
request_logs = []

MAX_LOGS = 100


# =============================================================================
# Authentication Helpers
# =============================================================================

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

        decoded_bytes = base64.b64decode(
            encoded_credentials
        )

        decoded_string = decoded_bytes.decode("utf-8")

        username, password = decoded_string.split(":", 1)

        valid_username = secrets.compare_digest(
            username,
            VALID_BASIC_USER,
        )

        valid_password = secrets.compare_digest(
            password,
            VALID_BASIC_PASS,
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
        VALID_BEARER_TOKEN,
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
    Validate API Key from header or query parameter.

    Returns:
        (success, authentication_type, message)
    """

    # X-API-Key
    if x_api_key:
        if secrets.compare_digest(
            x_api_key,
            VALID_API_KEY,
        ):
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

    # ApiKey header
    if api_key_header:
        if secrets.compare_digest(
            api_key_header,
            VALID_API_KEY,
        ):
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

    # Query parameter
    if query_api_key:
        if secrets.compare_digest(
            query_api_key,
            VALID_API_KEY,
        ):
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
    Validate any supported authentication method.

    Returns:
        (success, authentication_type, message)
    """

    if authorization:
        if authorization.startswith("Basic "):
            return check_basic_auth(
                authorization
            )

        if authorization.startswith("Bearer "):
            return check_bearer_token(
                authorization
            )

    return check_api_key(
        x_api_key=x_api_key,
        api_key_header=api_key_header,
        query_api_key=query_api_key,
    )


# =============================================================================
# Request Logging
# =============================================================================

def add_request_log(
    request: Request,
    auth_success: bool,
    authentication_type: str,
    auth_message: str,
    status_code: int,
    body,
):
    """
    Store an incoming request in the in-memory request history.
    """

    timestamp = datetime.now(
        timezone.utc
    ).astimezone().isoformat(
        timespec="seconds"
    )

    event = None
    request_id = None

    if isinstance(body, dict):
        event = body.get("event")
        request_id = body.get("id")

    log_entry = {
        "timestamp": timestamp,
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "remote_ip": (
            request.client.host
            if request.client
            else "Unknown"
        ),

        # Explicit authentication information
        "authentication_type": authentication_type,
        "authentication_success": auth_success,
        "authentication_message": auth_message,

        "status_code": status_code,

        # Useful for quickly identifying tests
        "event": event,
        "id": request_id,

        "headers": dict(request.headers),
        "query_parameters": dict(
            request.query_params
        ),
        "body": body,
    }

    request_logs.insert(
        0,
        log_entry,
    )

    if len(request_logs) > MAX_LOGS:
        del request_logs[MAX_LOGS:]


# =============================================================================
# Basic Authentication Endpoint
# =============================================================================

@app.get(
    "/basic/auth",
    tags=["Authentication"],
)
async def basic_auth(
    credentials: HTTPBasicCredentials = Depends(
        basic_security
    ),
):
    """
    Test Basic Authentication.

    Swagger:
        Click Authorize and enter the username/password.
    """

    valid_username = secrets.compare_digest(
        credentials.username,
        VALID_BASIC_USER,
    )

    valid_password = secrets.compare_digest(
        credentials.password,
        VALID_BASIC_PASS,
    )

    if not valid_username or not valid_password:
        raise HTTPException(
            status_code=401,
            detail="Invalid Basic Auth credentials",
            headers={
                "WWW-Authenticate": "Basic",
            },
        )

    return {
        "status": "success",
        "message": "Basic Authentication successful",
        "username": credentials.username,
    }


# =============================================================================
# OAuth / Bearer Authentication Endpoint
# =============================================================================

@app.get(
    "/oauth/protected",
    tags=["Authentication"],
)
async def oauth_protected(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_security
    ),
):
    """
    Test OAuth Bearer Token authentication.

    Swagger:
        Click Authorize and enter the Bearer token.
    """

    token = credentials.credentials

    if not secrets.compare_digest(
        token,
        VALID_BEARER_TOKEN,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid Bearer Token",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    return {
        "status": "success",
        "message": "OAuth Bearer Token is valid",
    }


# =============================================================================
# Webhook Receiver
# =============================================================================

@app.api_route(
    "/webhook",
    methods=["POST", "GET", "PUT"],
    tags=["Webhook"],
)
async def webhook_receiver(
    request: Request,
    authorization: Optional[str] = Header(
        default=None
    ),
    x_api_key: Optional[str] = Header(
        default=None
    ),
    api_key: Optional[str] = Header(
        default=None
    ),
):
    """
    Receive, authenticate, and inspect webhook requests.

    Supported authentication:

    - Basic Auth
    - OAuth / Bearer Token
    - X-API-Key
    - ApiKey
    - api_key query parameter
    """

    (
        auth_success,
        authentication_type,
        auth_message,
    ) = check_auth(
        authorization=authorization,
        x_api_key=x_api_key,
        api_key_header=api_key,
        query_api_key=request.query_params.get(
            "api_key"
        ),
    )

    # -------------------------------------------------------------------------
    # Read Request Body
    # -------------------------------------------------------------------------

    body = None

    try:
        raw_body = await request.body()

        if raw_body:
            content_type = request.headers.get(
                "content-type",
                "",
            )

            if "application/json" in content_type:
                try:
                    body = json.loads(
                        raw_body
                    )
                except json.JSONDecodeError:
                    body = raw_body.decode(
                        "utf-8",
                        errors="replace",
                    )
            else:
                body = raw_body.decode(
                    "utf-8",
                    errors="replace",
                )

    except Exception as exception:
        body = (
            f"Could not parse body: {exception}"
        )

    # -------------------------------------------------------------------------
    # Determine Response
    # -------------------------------------------------------------------------

    if not auth_success:
        status_code = 401

        response_content = {
            "status": "error",
            "message": auth_message,
            "authentication_type": authentication_type,
        }

    else:
        status_code = 200

        response_content = {
            "status": "success",
            "message": (
                "Webhook received and authenticated successfully"
            ),
            "authentication_type": authentication_type,
        }

    # -------------------------------------------------------------------------
    # Console Logging
    # -------------------------------------------------------------------------

    print("\n" + "=" * 70)
    print("📥 INCOMING WEBHOOK RECEIVED")
    print("=" * 70)

    print(f"Time: {datetime.now().astimezone()}")
    print(f"Method: {request.method}")
    print(f"URL: {request.url}")
    print(
        "Remote IP: "
        f"{request.client.host if request.client else 'Unknown'}"
    )

    print(
        f"Authentication: {authentication_type}"
    )

    print(
        f"Authentication Status: "
        f"{'🟢 SUCCESS' if auth_success else '🔴 FAILED'}"
    )

    print(f"Response Status: {status_code}")

    print("\n--- HEADERS ---")

    for header, value in request.headers.items():
        print(f"{header}: {value}")

    print("\n--- QUERY PARAMETERS ---")

    query_parameters = dict(
        request.query_params
    )

    print(
        json.dumps(
            query_parameters,
            indent=2,
        )
        if query_parameters
        else "None"
    )

    print("\n--- REQUEST BODY ---")

    if isinstance(body, (dict, list)):
        print(
            json.dumps(
                body,
                indent=2,
            )
        )
    elif body:
        print(body)
    else:
        print("Empty body")

    print("=" * 70 + "\n")

    # -------------------------------------------------------------------------
    # Store Request Log
    # -------------------------------------------------------------------------

    add_request_log(
        request=request,
        auth_success=auth_success,
        authentication_type=authentication_type,
        auth_message=auth_message,
        status_code=status_code,
        body=body,
    )

    return JSONResponse(
        status_code=status_code,
        content=response_content,
    )


# =============================================================================
# Logs - JSON
# =============================================================================

@app.get(
    "/logs/json",
    tags=["Logs"],
)
async def logs_json():
    """
    Return all received webhook requests as JSON.
    """

    return {
        "count": len(request_logs),
        "logs": request_logs,
    }


# =============================================================================
# Logs - Browser Dashboard
# =============================================================================

@app.get(
    "/logs",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def logs_dashboard():
    """
    Display received webhook requests in a browser.

    The page automatically refreshes every 5 seconds.
    """

    rows = []

    for log in request_logs:

        authentication_type = log[
            "authentication_type"
        ]

        status_code = log[
            "status_code"
        ]

        event = (
            log["event"]
            if log["event"]
            else "-"
        )

        request_id = (
            log["id"]
            if log["id"]
            else "-"
        )

        body = log["body"]

        if isinstance(
            body,
            (dict, list),
        ):
            formatted_body = json.dumps(
                body,
                indent=2,
            )
        elif body is None:
            formatted_body = "Empty body"
        else:
            formatted_body = str(body)

        headers = json.dumps(
            log["headers"],
            indent=2,
        )

        query_parameters = json.dumps(
            log["query_parameters"],
            indent=2,
        )

        auth_status = (
            "🟢 SUCCESS"
            if log["authentication_success"]
            else "🔴 FAILED"
        )

        rows.append(
            f"""
            <div class="request">

                <div class="top-row">

                    <div class="method">
                        {html.escape(log["method"])}
                    </div>

                    <div class="path">
                        {html.escape(log["path"])}
                    </div>

                    <div class="status">
                        HTTP {status_code}
                    </div>

                </div>

                <div class="metadata">

                    <div>
                        <strong>Time:</strong>
                        {html.escape(log["timestamp"])}
                    </div>

                    <div>
                        <strong>Authentication:</strong>
                        {html.escape(authentication_type)}
                    </div>

                    <div>
                        <strong>Result:</strong>
                        {auth_status}
                    </div>

                    <div>
                        <strong>Event:</strong>
                        {html.escape(str(event))}
                    </div>

                    <div>
                        <strong>ID:</strong>
                        {html.escape(str(request_id))}
                    </div>

                    <div>
                        <strong>Remote IP:</strong>
                        {html.escape(log["remote_ip"])}
                    </div>

                </div>

                <div class="message">
                    {html.escape(log["authentication_message"])}
                </div>

                <details>
                    <summary>Request Body</summary>
                    <pre>{html.escape(formatted_body)}</pre>
                </details>

                <details>
                    <summary>Headers</summary>
                    <pre>{html.escape(headers)}</pre>
                </details>

                <details>
                    <summary>Query Parameters</summary>
                    <pre>{html.escape(query_parameters)}</pre>
                </details>

                <div class="url">
                    <strong>URL:</strong>
                    {html.escape(log["url"])}
                </div>

            </div>
            """
        )

    request_rows = "".join(rows)

    if not request_rows:
        request_rows = """
        <div class="empty">
            No webhook requests received yet.
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>

    <html>

    <head>

        <title>API Mock Server - Logs</title>

        <meta
            http-equiv="refresh"
            content="5"
        >

        <meta
            name="viewport"
            content="width=device-width, initial-scale=1"
        >

        <style>

            body {{
                font-family: Arial, sans-serif;
                background: #f5f5f5;
                margin: 0;
                padding: 20px;
            }}

            .container {{
                max-width: 1200px;
                margin: auto;
            }}

            h1 {{
                margin-bottom: 5px;
            }}

            .subtitle {{
                color: #666;
                margin-bottom: 5px;
            }}

            .refresh {{
                color: #888;
                font-size: 13px;
                margin-bottom: 20px;
            }}

            .request {{
                background: white;
                border-radius: 8px;
                padding: 18px;
                margin-bottom: 15px;
                box-shadow:
                    0 2px 6px
                    rgba(0, 0, 0, 0.08);
            }}

            .top-row {{
                display: flex;
                gap: 15px;
                align-items: center;
                flex-wrap: wrap;
                margin-bottom: 15px;
            }}

            .method {{
                font-weight: bold;
                font-size: 16px;
            }}

            .path {{
                font-family: monospace;
            }}

            .status {{
                font-weight: bold;
            }}

            .metadata {{
                display: grid;
                grid-template-columns:
                    repeat(
                        auto-fit,
                        minmax(250px, 1fr)
                    );
                gap: 8px;
                margin-bottom: 12px;
            }}

            .message {{
                margin-bottom: 12px;
                font-weight: bold;
            }}

            details {{
                margin-top: 10px;
            }}

            summary {{
                cursor: pointer;
                font-weight: bold;
            }}

            pre {{
                background: #f0f0f0;
                padding: 12px;
                border-radius: 5px;
                overflow-x: auto;
                white-space: pre-wrap;
                word-break: break-word;
            }}

            .url {{
                margin-top: 12px;
                color: #555;
                word-break: break-all;
            }}

            .empty {{
                background: white;
                padding: 30px;
                text-align: center;
                border-radius: 8px;
                color: #666;
            }}

        </style>

    </head>

    <body>

        <div class="container">

            <h1>
                📋 API Mock Server Logs
            </h1>

            <div class="subtitle">
                Received requests:
                {len(request_logs)}
            </div>

            <div class="refresh">
                Automatically refreshes every 5 seconds.
            </div>

            {request_rows}

        </div>

    </body>

    </html>
    """

    return HTMLResponse(
        content=html_content
    )


# =============================================================================
# Clear Logs
# =============================================================================

@app.delete(
    "/logs",
    tags=["Logs"],
)
async def clear_logs():
    """Clear all stored request logs."""

    request_logs.clear()

    return {
        "status": "success",
        "message": "Request logs cleared",
    }


# =============================================================================
# Health Check
# =============================================================================

@app.get(
    "/",
    tags=["Health"],
)
async def health_check():
    """Check whether the mock API is running."""

    return {
        "application": "API Mock Server",
        "status": "running",
        "endpoints": {
            "basic_auth": "GET /basic/auth",
            "oauth_protected": "GET /oauth/protected",
            "webhook": "POST /webhook",
            "logs": "GET /logs",
            "logs_json": "GET /logs/json",
            "clear_logs": "DELETE /logs",
            "swagger": "GET /docs",
        },
    }


# =============================================================================
# Application Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
# Localhosting
    uvicorn.run(
        "mock_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
# Cloud with random Port
# uvicorn mock_api:app --host 0.0.0.0 --port $PORT
