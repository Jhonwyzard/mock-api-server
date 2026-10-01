import base64
import os
import secrets
from fastapi import APIRouter, Depends, Form, HTTPException, Request, WebSocket, WebSocketDisconnect

from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from ..config import settings
from ..core.logger import log_store
from ..core.security import get_logs_basic_auth

router = APIRouter(tags=["Logs"])

# Path to the templates directory
TEMPLATES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates"
)
DASHBOARD_PATH = os.path.join(TEMPLATES_DIR, "dashboard.html")
LOGIN_PATH = os.path.join(TEMPLATES_DIR, "login.html")


@router.get("/logs/login", response_class=HTMLResponse, include_in_schema=False)
async def logs_login_page():
    """Display modern glassmorphism login form for request logs dashboard."""
    try:
        with open(LOGIN_PATH, "r", encoding="utf-8") as file:
            return HTMLResponse(content=file.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Login Template Not Found</h1><p>Please check app/templates/login.html</p>",
            status_code=500,
        )


@router.post("/logs/login", include_in_schema=False)
async def logs_login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    """Authenticate user credentials and set dashboard session cookie."""
    if len(username) > 100 or len(password) > 200:
        raise HTTPException(
            status_code=400,
            detail="Payload size exceeded",
        )

    logs_user = getattr(settings, "LOGS_BASIC_USER", getattr(settings, "VALID_BASIC_USER", "admin"))
    logs_pass = getattr(settings, "LOGS_BASIC_PASS", getattr(settings, "VALID_BASIC_PASS", "secretpassword"))

    valid_user = secrets.compare_digest(username, logs_user)
    valid_pass = secrets.compare_digest(password, logs_pass)

    if not valid_user or not valid_pass:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    # Generate session token cookie
    token_str = f"{logs_user}:{logs_pass}"
    session_token = base64.b64encode(token_str.encode("utf-8")).decode("utf-8")

    is_secure = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"

    response = JSONResponse(content={"status": "success", "message": "Logged in successfully"})
    response.set_cookie(
        key="logs_session",
        value=session_token,
        max_age=86400 * 7,  # 7 days session
        httponly=True,
        samesite="lax",
        secure=is_secure,
    )
    return response



@router.post("/logs/logout", include_in_schema=False)
async def logs_logout():
    """Clear session cookie and log out of request logs dashboard."""
    response = JSONResponse(content={"status": "success", "message": "Logged out"})
    response.delete_cookie(key="logs_session")
    return response


@router.get("/logs", response_class=HTMLResponse, include_in_schema=False)
async def logs_dashboard(user: str | None = Depends(get_logs_basic_auth)):
    """
    Display received webhook requests in a browser using a premium interactive dashboard.
    """
    if user is None:
        return RedirectResponse(url="/logs/login", status_code=303)

    try:
        with open(DASHBOARD_PATH, "r", encoding="utf-8") as file:
            html_content = file.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Dashboard Template Not Found</h1><p>Please check app/templates/dashboard.html</p>",
            status_code=500,
        )



@router.get("/logs/json")
async def logs_json(_: str = Depends(get_logs_basic_auth)):
    """
    Return all received webhook requests as JSON.
    """
    return {
        "count": log_store.count(),
        "logs": log_store.get_all(),
    }


@router.delete("/logs")
async def clear_logs(_: str = Depends(get_logs_basic_auth)):
    """Clear all stored request logs."""

    log_store.clear()
    await log_store.broadcast_update()
    return {
        "status": "success",
        "message": "Request logs cleared",
    }


@router.websocket("/logs/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint to push updates when new webhook messages arrive."""
    await log_store.connect(websocket)
    try:
        while True:
            # Keep client connection alive by waiting for messages (none expected)
            await websocket.receive_text()
    except WebSocketDisconnect:
        log_store.disconnect(websocket)

