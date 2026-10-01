import json
from datetime import datetime
from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from ..core.logger import log_store
from ..core.security import check_auth

router = APIRouter(tags=["Webhook"])


@router.api_route("/webhook", methods=["POST", "GET", "PUT"])
@router.api_route("/webhook/{path:path}", methods=["POST", "GET", "PUT"])
async def webhook_receiver(
    request: Request,
    path: str | None = None,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
    api_key: str | None = Header(default=None),
):
    """
    Receive, authenticate, and inspect webhook requests.

    Supported authentication:
    - Basic Auth
    - OAuth / Bearer Token
    - X-API-Key (Header)
    - ApiKey (Header)
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
        query_api_key=request.query_params.get("api_key"),
    )

    # -------------------------------------------------------------------------
    # Read Request Body
    # -------------------------------------------------------------------------
    body = None

    try:
        raw_body = await request.body()
        if raw_body:
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    body = json.loads(raw_body)
                except json.JSONDecodeError:
                    body = raw_body.decode("utf-8", errors="replace")
            else:
                body = raw_body.decode("utf-8", errors="replace")
    except Exception as exception:
        body = f"Could not parse body: {exception}"

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
            "message": "Webhook received and authenticated successfully",
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
        f"Remote IP: {request.client.host if request.client else 'Unknown'}"
    )
    print(f"Authentication: {authentication_type}")
    print(
        f"Authentication Status: "
        f"{'🟢 SUCCESS' if auth_success else '🔴 FAILED'}"
    )
    print(f"Response Status: {status_code}")

    print("\n--- HEADERS ---")
    for header, value in request.headers.items():
        print(f"{header}: {value}")

    print("\n--- QUERY PARAMETERS ---")
    query_parameters = dict(request.query_params)
    print(
        json.dumps(query_parameters, indent=2)
        if query_parameters
        else "None"
    )

    print("\n--- REQUEST BODY ---")
    if isinstance(body, (dict, list)):
        print(json.dumps(body, indent=2))
    elif body:
        print(body)
    else:
        print("Empty body")
    print("=" * 70 + "\n")

    # -------------------------------------------------------------------------
    # Store Request Log
    # -------------------------------------------------------------------------
    log_store.add_log(
        request=request,
        auth_success=auth_success,
        authentication_type=authentication_type,
        auth_message=auth_message,
        status_code=status_code,
        body=body,
    )
    await log_store.broadcast_update()

    return JSONResponse(
        status_code=status_code,
        content=response_content,
        headers={"WWW-Authenticate": "Basic"} if status_code == 401 else {},
    )
