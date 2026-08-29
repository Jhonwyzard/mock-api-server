# Mock API Server - AI Agent Guidelines & Repository Map

Welcome, AI Developer! This workspace is optimized for token-efficient comprehension. Do NOT read the entire codebase. Follow the map and coding style rules below.

---

## ⚡ Token-Saving Architecture Map

To modify or enhance this codebase without consuming high amounts of context tokens, refer to this mapping instead of loading all files:

```
mock-api-server/
├── app/
│   ├── config.py           # [READ FIRST] Config & Env variables. Dictates auth secrets & size limits.
│   ├── main.py             # App registration. Start here to inspect registered routers.
│   ├── core/
│   │   ├── security.py     # Auth algorithms (Basic, Bearer, Key). Check here to add auth types.
│   │   └── logger.py       # Thread-safe LogStore. Check here to alter data schema or storage.
│   ├── routers/
│   │   ├── auth.py         # Routes checking Basic / Bearer tokens.
│   │   ├── webhook.py      # Route receiving payloads. Reads body, prints console, logs data.
│   │   └── logs.py         # Routes feeding logs list, clearing logs, and rendering UI.
│   └── templates/
│       └── dashboard.html  # Logs UI. Single-page JS application (Fetch, search, copy payloads).
└── tests/                  # Pytest verification suites. Mirror route changes here.
```

### Quick Reference for Token Conservation:
* **To check API models/endpoints**: Read [openapi.json](file:///m:/Personal/Workspaces/mock-api-server/openapi.json). Do not load python code router files.
* **To alter credentials**: Edit [app/config.py](file:///m:/Personal/Workspaces/mock-api-server/app/config.py).
* **To modify webhook authentication**: Edit [app/core/security.py](file:///m:/Personal/Workspaces/mock-api-server/app/core/security.py) and [app/routers/webhook.py](file:///m:/Personal/Workspaces/mock-api-server/app/routers/webhook.py).

---

## 🛠️ Code Styling & Implementation Rules

Ensure any future code enhancements follow these guidelines:

### 1. Relative Imports
* Inside the `app` package, **always use explicit relative imports** (e.g., `from ..config import settings` rather than `from app.config import settings`).
* This enables IDEs to correctly resolve package submodules and prevents import path breaks.

### 2. Thread Safety
* The memory log database in [app/core/logger.py](file:///m:/Personal/Workspaces/mock-api-server/app/core/logger.py) must remain thread-safe.
* Any read/write operations on `LogStore._logs` must be performed within the `with self._lock:` context manager to prevent race conditions during concurrent webhook submissions.

### 3. Auth Sequence Fallthrough
* The `/webhook` receiver router must try authentication protocols sequentially (Basic Auth -> Bearer Token -> X-API-Key -> ApiKey -> query api_key).
* Requests with invalid or missing auth **must still be logged** in `LogStore` with `authentication_success=False`, and return a `401` status.

### 4. HTML Dashboard Code Separation
* The dashboard page [app/templates/dashboard.html](file:///m:/Personal/Workspaces/mock-api-server/app/templates/dashboard.html) must remain a separated static HTML template.
* Do not embed layout HTML strings directly in python router code files. Load the file from `DASHBOARD_PATH` inside [app/routers/logs.py](file:///m:/Personal/Workspaces/mock-api-server/app/routers/logs.py).

### 5. Wildcard Webhook Subpaths
* Webhook requests directed to `/webhook/{path:path}` are dynamically matched to permit testing of subpaths (e.g. `/webhook/devices/ID001`). Ensure the captured path is fully logged.

### 6. Real-time WebSocket Updates
* The dashboard utilizes a WebSocket connection on `/logs/ws` for instant real-time pushes.
* Whenever a new request is logged or cleared, the backend must call `await log_store.broadcast_update()` to notify active WebSocket connections.
* Ensure WebSocket connections are handled gracefully and safely disconnected to prevent resource leaks.

---

## 🧪 Testing Guidelines

* Every new feature, endpoint, or authentication type **must** include accompanying unit and integration tests in the `tests/` folder.
* **Fixture Usage**: Always use the `client` fixture defined in [tests/conftest.py](file:///m:/Personal/Workspaces/mock-api-server/tests/conftest.py). It automatically cleans and purges the `log_store` database before and after each test case to guarantee isolated test runs.
* Run tests locally using `pytest -v` to ensure nothing is broken.
