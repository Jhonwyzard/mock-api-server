# Mock API Server - AI Agent Guidelines & Repository Map

Welcome, AI Developer! This workspace is optimized for token-efficient comprehension. Do NOT read the entire codebase. Follow the map and coding style rules below.

---

## ⚡ Token-Saving Architecture Map

To modify or enhance this codebase without consuming high amounts of context tokens, refer to this mapping instead of loading all files:

```
mock-api-server/
├── app/
│   ├── config.py           # [READ FIRST] Config & Env variables (MOCK_REQUIRE_AUTH, MOCK_RATE_LIMIT_PER_SEC, etc.).
│   ├── main.py             # App registration & RateLimit middleware. Start here to inspect registered routers.
│   ├── core/
│   │   ├── security.py     # Auth algorithms (Basic, Bearer, Key, Cookie). Check here to add auth types.
│   │   ├── logger.py       # Thread-safe LogStore. Check here to alter data schema or storage.
│   │   └── rate_limiter.py # Thread-safe sliding window RateLimiter per IP.
│   ├── routers/
│   │   ├── auth.py         # Routes checking Basic / Bearer tokens.
│   │   ├── webhook.py      # Route receiving payloads. Reads body, prints console, logs data.
│   │   └── logs.py         # Routes for logs dashboard, login/logout, JSON logs, and clear logs.
│   └── templates/
│       ├── dashboard.html  # Logs UI. Single-page JS application (Fetch, search, copy payloads).
│       └── login.html      # Simple, secure login page for logs dashboard session authentication.
└── tests/                  # Pytest verification suites. Mirror route changes here.
```

### Quick Reference for Token Conservation:
* **To check API models/endpoints**: Read [openapi.json](file:///m:/Personal/Workspaces/mock-api-server/openapi.json). Do not load python code router files.
* **To alter credentials or env flags**: Edit [app/config.py](file:///m:/Personal/Workspaces/mock-api-server/app/config.py).
* **To modify rate limiting**: Edit [app/core/rate_limiter.py](file:///m:/Personal/Workspaces/mock-api-server/app/core/rate_limiter.py) and `rate_limit_middleware` in [app/main.py](file:///m:/Personal/Workspaces/mock-api-server/app/main.py).
* **To modify webhook authentication**: Edit [app/core/security.py](file:///m:/Personal/Workspaces/mock-api-server/app/core/security.py) and [app/routers/webhook.py](file:///m:/Personal/Workspaces/mock-api-server/app/routers/webhook.py).
* **To modify logs authentication / login**: Edit [app/core/security.py](file:///m:/Personal/Workspaces/mock-api-server/app/core/security.py) and [app/routers/logs.py](file:///m:/Personal/Workspaces/mock-api-server/app/routers/logs.py).

---

## 🛠️ Code Styling & Implementation Rules

Ensure any future code enhancements follow these guidelines:

### 1. Relative Imports
* Inside the `app` package, **always use explicit relative imports** (e.g., `from ..config import settings` rather than `from app.config import settings`).
* This enables IDEs to correctly resolve package submodules and prevents import path breaks.

### 2. Thread Safety
* The memory log database in [app/core/logger.py](file:///m:/Personal/Workspaces/mock-api-server/app/core/logger.py) and rate limiter in [app/core/rate_limiter.py](file:///m:/Personal/Workspaces/mock-api-server/app/core/rate_limiter.py) must remain thread-safe.
* Any read/write operations on shared state must be performed within `with self._lock:` context managers to prevent race conditions under concurrent requests.

### 3. Auth Sequence Fallthrough & Toggles
* The `/webhook` receiver router must try authentication protocols sequentially (Basic Auth -> Bearer Token -> X-API-Key -> ApiKey -> query api_key).
* When `MOCK_REQUIRE_AUTH` is `true` (default), requests with invalid or missing auth must still be logged in `LogStore` with `authentication_success=False`, and return a `401` status.
* When `MOCK_REQUIRE_AUTH` is `false`, unauthenticated requests are allowed and logged as `ANONYMOUS / NONE`.

### 4. HTML Templates Code Separation & Security
* Static HTML files ([dashboard.html](file:///m:/Personal/Workspaces/mock-api-server/app/templates/dashboard.html), [login.html](file:///m:/Personal/Workspaces/mock-api-server/app/templates/login.html)) must remain separated templates under `app/templates/`.
* Do not embed layout HTML strings directly in python router files. Load templates from `DASHBOARD_PATH` or `LOGIN_PATH` inside [app/routers/logs.py](file:///m:/Personal/Workspaces/mock-api-server/app/routers/logs.py).
* **Security & Placeholders**: Never use hardcoded credentials or example account names (e.g. `admin`) as input placeholders in login forms. Use standard, neutral placeholders (`Username`, `Password`), with HTML5 security attributes (`autocomplete="username"`, `autocomplete="current-password"`, `spellcheck="false"`).

### 5. Wildcard Webhook Subpaths
* Webhook requests directed to `/webhook/{path:path}` are dynamically matched to permit testing of subpaths (e.g. `/webhook/devices/ID001`). Ensure the captured path is fully logged.

### 6. Real-time WebSocket Updates
* The dashboard utilizes a WebSocket connection on `/logs/ws` for instant real-time pushes.
* Whenever a new request is logged or cleared, the backend must call `await log_store.broadcast_update()` to notify active WebSocket connections.
* Ensure WebSocket connections are handled gracefully and safely disconnected to prevent resource leaks.

### 7. Rate Limiting & Scripting Attack Protection
* **Sliding Window Rate Limiting**: All HTTP endpoints are protected by `rate_limit_middleware` in [app/main.py](file:///m:/Personal/Workspaces/mock-api-server/app/main.py). Default rate limit is **10 requests per second per IP** (`MOCK_RATE_LIMIT_PER_SEC=10`). Requests exceeding the rate limit receive HTTP `429 Too Many Requests`.
* **Timing Attack Prevention**: Always use `secrets.compare_digest()` for password and token comparisons.
* **Payload Length Limits**: Validate and cap form field lengths (e.g. username/password input limits) to prevent memory exhaustion and ReDoS attacks.
* **Secure Cookies**: Session cookies must be set with `HttpOnly=True`, `SameSite="Lax"`, and `Secure=True` on HTTPS connections.

---

## 🧪 Testing Guidelines

* Every new feature, endpoint, or authentication type **must** include accompanying unit and integration tests in the `tests/` folder.
* **Fixture Usage**: Always use the `client` fixture defined in [tests/conftest.py](file:///m:/Personal/Workspaces/mock-api-server/tests/conftest.py). It automatically cleans and purges the `log_store` database before and after each test case to guarantee isolated test runs.
* Run tests locally using `pytest -v` to ensure nothing is broken.


