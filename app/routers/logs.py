import os
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from ..core.logger import log_store
from ..core.security import get_logs_basic_auth

router = APIRouter(tags=["Logs"])

# Path to the templates directory
TEMPLATES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates"
)
DASHBOARD_PATH = os.path.join(TEMPLATES_DIR, "dashboard.html")


@router.get("/logs", response_class=HTMLResponse, include_in_schema=False)
async def logs_dashboard(_: str = Depends(get_logs_basic_auth)):
    """
    Display received webhook requests in a browser using a premium interactive dashboard.
    """
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

