import threading
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import Request, WebSocket
from ..config import settings


class LogStore:
    """Thread-safe, in-memory log storage for incoming requests."""

    def __init__(self):
        self._logs: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self._active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self._active_connections:
            self._active_connections.remove(websocket)

    async def broadcast_update(self):
        """Notify all connected WebSockets that a new log has arrived."""
        for connection in list(self._active_connections):
            try:
                await connection.send_text("update")
            except Exception:
                if connection in self._active_connections:
                    self._active_connections.remove(connection)

    def add_log(
        self,
        request: Request,
        auth_success: bool,
        authentication_type: str,
        auth_message: str,
        status_code: int,
        body: Any,
    ) -> Dict[str, Any]:
        """
        Construct and append a log entry thread-safely.
        Limits log entries to settings.MAX_LOGS.
        """
        timestamp = (
            datetime.now(timezone.utc)
            .astimezone()
            .isoformat(timespec="seconds")
        )

        log_entry = {
            "timestamp": timestamp,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "remote_ip": (
                request.client.host if request.client else "Unknown"
            ),
            "authentication_type": authentication_type,
            "authentication_success": auth_success,
            "authentication_message": auth_message,
            "status_code": status_code,
            "headers": dict(request.headers),
            "query_parameters": dict(request.query_params),
            "body": body,
        }

        with self._lock:
            self._logs.insert(0, log_entry)
            if len(self._logs) > settings.MAX_LOGS:
                del self._logs[settings.MAX_LOGS :]

        return log_entry

    def clear(self):
        """Clear all stored logs thread-safely."""
        with self._lock:
            self._logs.clear()

    def get_all(self) -> List[Dict[str, Any]]:
        """Return a copy of all stored logs thread-safely."""
        with self._lock:
            return list(self._logs)

    def count(self) -> int:
        """Return logs count thread-safely."""
        with self._lock:
            return len(self._logs)


log_store = LogStore()
