# API Mock Server

A generic local Python mock server for testing API integrations, authentication, and webhooks.

The server is built with **FastAPI** and provides:

* Basic Authentication
* OAuth / Bearer Token authentication
* API Key authentication
* Swagger UI testing
* Webhook request body logging
* Request header logging
* Query parameter logging
* Authentication result logging
* Authentication type identification
* Browser-based request log dashboard
* JSON request log endpoint
* ngrok support for external webhook testing

---

# Requirements

* Python 3.13+
* pip
* Optional: ngrok, if external systems need to access the local server

Check Python:

```bash
python --version
```

Check pip:

```bash
pip --version
```

If using ngrok:

```bash
ngrok version
```

---

# Project Structure

```text
api-mock/
│
├── app/
│   ├── __init__.py
│   ├── main.py             # FastAPI app initialization, routes registration
│   ├── config.py           # Configuration settings, credentials, env vars
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py     # Auth helpers (Basic, OAuth, API key)
│   │   └── logger.py       # Thread-safe in-memory log store
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py         # Routes for GET /basic/auth, GET /oauth/protected
│   │   ├── webhook.py      # Routes for GET/POST/PUT /webhook
│   │   └── logs.py         # Routes for GET/DELETE /logs and GET /logs/json
│   └── templates/
│       └── dashboard.html  # Premium request log dashboard (HTML/CSS/JS)
│
├── tests/                  # Automated tests to ensure maintainability
│   ├── __init__.py
│   ├── conftest.py         # Test client fixture and setup
│   ├── test_auth.py        # Test auth endpoints
│   ├── test_webhook.py     # Test webhook endpoints
│   └── test_logs.py        # Test logs endpoints
│
├── mock_api.py             # Lightweight entrypoint wrapper (backwards-compatible)
├── requirements.txt        # Package and testing dependencies
├── README.md
└── .gitignore
```

---

# Python Installation

## Install Dependencies

From the project directory:

```bash
pip install -r requirements.txt
```

The `requirements.txt` contains:

```text
fastapi
uvicorn[standard]
python-multipart

# Dev & testing dependencies
pytest
httpx
```

---

# Start the Server

Run:

```bash
python mock_api.py
```

The server will start on:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/
```

FastAPI Swagger UI:

```text
http://localhost:8000/docs
```

Swagger UI can be used to test the authentication endpoints directly.

---

# Available Endpoints

| Method   | Endpoint           | Purpose                             |
| -------- | ------------------ | ----------------------------------- |
| `GET`    | `/`                | Health check                        |
| `GET`    | `/basic/auth`      | Test Basic Authentication           |
| `GET`    | `/oauth/protected` | Test OAuth / Bearer Token           |
| `POST`   | `/webhook` or `/webhook/*` | Receive authenticated webhook under main or subpaths |
| `GET`    | `/webhook` or `/webhook/*` | Receive/test webhook under main or subpaths          |
| `PUT`    | `/webhook` or `/webhook/*` | Receive/test webhook under main or subpaths          |
| `GET`    | `/logs`            | Browser-based request log dashboard |
| `GET`    | `/logs/json`       | Return request logs as JSON         |
| `DELETE` | `/logs`            | Clear request logs                  |
| `WS`     | `/logs/ws`         | Real-time WebSocket update push     |
| `GET`    | `/docs`            | Swagger UI                          |

---

# Webhook Endpoint

The webhook endpoint accepts requests on the main route as well as any subpath:

```text
POST /webhook
POST /webhook/{any/subpath/or/device/id}
```

The same endpoint supports:

1. Basic Authentication
2. OAuth / Bearer Token
3. X-API-Key
4. ApiKey header
5. API key query parameter

All requests are logged, including:

* Timestamp
* HTTP method
* URL
* Remote IP
* Authentication type
* Authentication result
* HTTP response status
* Event
* Request ID
* Request headers
* Query parameters
* Request body

---

# Authentication

## Basic Authentication

Test credentials:

```text
Username: admin
Password: secretpassword
```

### cURL

```bash
curl -X POST http://localhost:8000/webhook \
  -u admin:secretpassword \
  -H "Content-Type: application/json" \
  -d "{\"event\":\"Test Basic Auth\",\"id\":\"BASIC-001\",\"message\":\"Testing Basic Authentication\"}"
```

Expected payload:

```json
{
  "event": "Test Basic Auth",
  "id": "BASIC-001",
  "message": "Testing Basic Authentication"
}
```

Expected response:

```json
{
  "status": "success",
  "message": "Webhook received and authenticated successfully",
  "authentication_type": "BASIC AUTH"
}
```

---

# OAuth / Bearer Token

The mock server uses a fixed OAuth-style Bearer token.

```text
Bearer Token: oauth-token-xyz-789
```

### cURL

```bash
curl -X POST http://localhost:8000/webhook \
  -H "Authorization: Bearer oauth-token-xyz-789" \
  -H "Content-Type: application/json" \
  -d "{\"event\":\"Test OAuth Bearer\",\"id\":\"OAUTH-002\",\"message\":\"Testing OAuth Bearer Token Authentication\"}"
```

Expected payload:

```json
{
  "event": "Test OAuth Bearer",
  "id": "OAUTH-002",
  "message": "Testing OAuth Bearer Token Authentication"
}
```

Expected response:

```json
{
  "status": "success",
  "message": "Webhook received and authenticated successfully",
  "authentication_type": "OAUTH / BEARER TOKEN"
}
```

> The mock server does not generate or renew OAuth tokens. It uses a fixed token for testing authentication.

---

# API Key

Test API key:

```text
my-super-secret-api-key-123
```

## X-API-Key

```bash
curl -X POST http://localhost:8000/webhook \
  -H "X-API-Key: my-super-secret-api-key-123" \
  -H "Content-Type: application/json" \
  -d "{\"event\":\"Test X-API-Key\",\"id\":\"APIKEY-003\",\"message\":\"Testing X-API-Key Authentication\"}"
```

Expected payload:

```json
{
  "event": "Test X-API-Key",
  "id": "APIKEY-003",
  "message": "Testing X-API-Key Authentication"
}
```

Expected authentication type in the logs:

```text
X-API-KEY
```

---

# ApiKey Header

The server also accepts:

```http
ApiKey: my-super-secret-api-key-123
```

Example:

```bash
curl -X POST http://localhost:8000/webhook \
  -H "ApiKey: my-super-secret-api-key-123" \
  -H "Content-Type: application/json" \
  -d "{\"event\":\"Test ApiKey Header\",\"id\":\"APIKEY-004\",\"message\":\"Testing ApiKey Header Authentication\"}"
```

Expected authentication type:

```text
APIKEY HEADER
```

---

# API Key Query Parameter

The API key can also be passed as a query parameter:

```bash
curl -X POST "http://localhost:8000/webhook?api_key=my-super-secret-api-key-123" \
  -H "Content-Type: application/json" \
  -d "{\"event\":\"Test API Key Query\",\"id\":\"APIKEY-005\",\"message\":\"Testing Query Parameter API Key\"}"
```

Expected authentication type:

```text
QUERY PARAMETER API KEY
```

---

# Swagger Testing

Swagger UI is available at:

```text
http://localhost:8000/docs
```

Open Swagger and click:

```text
Authorize
```

The application exposes the following security schemes:

* `BasicAuth`
* `BearerAuth`

---

## Testing Basic Authentication

In Swagger:

1. Open:

   ```text
   GET /basic/auth
   ```

2. Click **Authorize**.

3. Enter:

   ```text
   Username: admin
   Password: secretpassword
   ```

4. Click **Authorize**.

5. Execute:

   ```text
   GET /basic/auth
   ```

Expected response:

```json
{
  "status": "success",
  "message": "Basic Authentication successful",
  "username": "admin"
}
```

---

## Testing OAuth / Bearer Token

In Swagger:

1. Click **Authorize**.

2. Select `BearerAuth`.

3. Enter:

   ```text
   oauth-token-xyz-789
   ```

4. Click **Authorize**.

Swagger will send:

```http
Authorization: Bearer oauth-token-xyz-789
```

Then execute:

```text
GET /oauth/protected
```

Expected response:

```json
{
  "status": "success",
  "message": "OAuth Bearer Token is valid"
}
```

---

# Webhook Request Logging

Every request to `/webhook` is logged to the application console.

For example:

```text
======================================================================
📥 INCOMING WEBHOOK RECEIVED
======================================================================
Time: 2026-08-29T21:30:00+08:00
Method: POST
URL: http://localhost:8000/webhook
Remote IP: 127.0.0.1

Authentication: BASIC AUTH
Authentication Status: 🟢 SUCCESS
Response Status: 200

--- HEADERS ---
Host: localhost:8000
Authorization: Basic ...
Content-Type: application/json

--- QUERY PARAMETERS ---
None

--- REQUEST BODY ---
{
  "event": "Test Basic Auth",
  "id": "BASIC-001",
  "message": "Testing Basic Authentication"
}
======================================================================
```

For OAuth:

```text
======================================================================
📥 INCOMING WEBHOOK RECEIVED
======================================================================
Time: 2026-08-29T21:31:00+08:00
Method: POST
URL: http://localhost:8000/webhook
Remote IP: 127.0.0.1

Authentication: OAUTH / BEARER TOKEN
Authentication Status: 🟢 SUCCESS
Response Status: 200

--- HEADERS ---
Host: localhost:8000
Authorization: Bearer ...
Content-Type: application/json

--- QUERY PARAMETERS ---
None

--- REQUEST BODY ---
{
  "event": "Test OAuth Bearer",
  "id": "OAUTH-002",
  "message": "Testing OAuth Bearer Token Authentication"
}
======================================================================
```

This makes it easy to identify:

```text
Which authentication method was used?
What event was sent?
What request ID was sent?
What payload was received?
Was authentication successful?
What HTTP response was returned?
```

---

# Browser Log Dashboard

The application provides a browser-based log dashboard:

```text
http://localhost:8000/logs
```

Open it in a browser while the mock server is running.

The dashboard displays:

* Timestamp
* HTTP method
* Endpoint path
* HTTP status
* Authentication type
* Authentication result
* Remote IP
* Request body
* Headers
* Query parameters

The dashboard updates in real time using WebSockets (with a 10-second polling fallback if the WebSocket is disconnected).

Example:

```text
API Mock Server Logs

Received requests: 3
Automatically refreshes every 5 seconds.


POST   /webhook   HTTP 200

Time: 2026-08-29T21:30:00+08:00
Authentication: BASIC AUTH
Result: 🟢 SUCCESS
Event: Test Basic Auth
ID: BASIC-001
Remote IP: 127.0.0.1

> Request Body
> Headers
> Query Parameters
```

This is useful when sharing the mock server with your team because they can see the received requests from a browser instead of looking at the terminal.

---

# JSON Logs

The request history is also available as JSON:

```text
http://localhost:8000/logs/json
```

Example:

```json
{
  "count": 1,
  "logs": [
    {
      "timestamp": "2026-08-29T21:30:00+08:00",
      "method": "POST",
      "url": "http://localhost:8000/webhook",
      "path": "/webhook",
      "remote_ip": "127.0.0.1",
      "authentication_type": "BASIC AUTH",
      "authentication_success": true,
      "authentication_message": "Authenticated via Basic Auth",
      "status_code": 200,
      "headers": {},
      "query_parameters": {},
      "body": {
        "event": "Test Basic Auth",
        "id": "BASIC-001",
        "message": "Testing Basic Authentication"
      }
    }
  ]
}
```

This endpoint can also be used by another application to consume the mock server's request history.

---

# Clear Logs

To clear the request history:

```bash
curl -X DELETE http://localhost:8000/logs
```

Expected response:

```json
{
  "status": "success",
  "message": "Request logs cleared"
}
```

> Logs are stored in memory. Restarting the application also clears the logs.

---

# Testing Without Authentication

You can test an unauthenticated request:

```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d "{\"event\":\"Test No Authentication\",\"id\":\"NOAUTH-006\",\"message\":\"Testing Unauthorized Request\"}"
```

The request is still logged.

Expected response:

```json
{
  "status": "error",
  "message": "Missing API Key",
  "authentication_type": "NONE / INVALID"
}
```

HTTP status:

```text
401 Unauthorized
```

The log will show:

```text
Authentication: NONE / INVALID
Authentication Status: 🔴 FAILED
Response Status: 401
```

---

# ngrok

ngrok can expose the local FastAPI server to external systems.

The basic flow is:

```text
External System
       |
       | HTTPS
       v
    ngrok
       |
       | HTTP
       v
localhost:8000
       |
       v
   /webhook
```

This is useful when a cloud integration needs to send a webhook to your local mock server.

---

# Install ngrok on Windows

## Option 1: WinGet

Open **Command Prompt** or **PowerShell**:

```cmd
winget install ngrok -s msstore
```

Close and reopen the terminal after installation.

Verify:

```cmd
ngrok version
```

If Windows security or company policies block the ngrok executable, use another approved method or deployment environment instead.

---

## Option 2: Download ngrok

Download ngrok from the official ngrok website and install it according to the Windows instructions.

After installation:

```cmd
ngrok version
```

---

# Install ngrok on macOS

## Homebrew

If Homebrew is installed:

```bash
brew install ngrok
```

Verify:

```bash
ngrok version
```

Alternatively, install ngrok using the official macOS installation instructions.

---

# Configure ngrok

After installing ngrok, configure your ngrok authentication token.

Run:

```bash
ngrok config add-authtoken "<YOUR_AUTHTOKEN>"
```

Verify:

```bash
ngrok version
```

---

# Start ngrok

First start the FastAPI application:

```bash
python mock_api.py
```

The API should be available at:

```text
http://localhost:8000
```

Open another terminal:

```bash
ngrok http 8000
```

ngrok will provide a public URL similar to:

```text
https://abc123.ngrok-free.app
```

Your public webhook URL becomes:

```text
https://abc123.ngrok-free.app/webhook
```

---

# Testing Through ngrok

Replace:

```text
https://abc123.ngrok-free.app
```

with your actual ngrok URL.

## Basic Authentication

```bash
curl -X POST https://abc123.ngrok-free.app/webhook \
  -u admin:secretpassword \
  -H "Content-Type: application/json" \
  -d "{\"event\":\"Test Basic Auth - ngrok\",\"id\":\"NGROK-BASIC-101\",\"message\":\"Testing Basic Authentication through ngrok\"}"
```

Expected authentication type:

```text
BASIC AUTH
```

---

## OAuth / Bearer Token

```bash
curl -X POST https://abc123.ngrok-free.app/webhook \
  -H "Authorization: Bearer oauth-token-xyz-789" \
  -H "Content-Type: application/json" \
  -d "{\"event\":\"Test OAuth Bearer - ngrok\",\"id\":\"NGROK-OAUTH-102\",\"message\":\"Testing OAuth Bearer Token through ngrok\"}"
```

Expected authentication type:

```text
OAUTH / BEARER TOKEN
```

---

## API Key

```bash
curl -X POST https://abc123.ngrok-free.app/webhook \
  -H "X-API-Key: my-super-secret-api-key-123" \
  -H "Content-Type: application/json" \
  -d "{\"event\":\"Test API Key - ngrok\",\"id\":\"NGROK-APIKEY-103\",\"message\":\"Testing API Key through ngrok\"}"
```

Expected authentication type:

```text
X-API-KEY
```

---

# Authentication Summary

| Authentication | Method      | Location        | Supported |
| -------------- | ----------- | --------------- | --------- |
| Basic Auth     | `Basic`     | `Authorization` | ✅         |
| OAuth / Bearer | `Bearer`    | `Authorization` | ✅         |
| API Key        | `X-API-Key` | Header          | ✅         |
| API Key        | `ApiKey`    | Header          | ✅         |
| API Key        | `api_key`   | Query parameter | ✅         |

All authentication methods can be tested against:

```text
POST /webhook
```

---

# Test Credentials

These credentials are intended for local development and testing only.

| Purpose        | Value                         |
| -------------- | ----------------------------- |
| Basic Username | `admin`                       |
| Basic Password | `secretpassword`              |
| Bearer Token   | `oauth-token-xyz-789`         |
| API Key        | `my-super-secret-api-key-123` |
| Port           | `8000`                        |

Do not use these credentials in production.

---

# Recommended Test Payloads

Use a different `event` and `id` for each test scenario.

This makes it easy to identify which authentication test generated a webhook.

| Test              | Event                       | ID                 |
| ----------------- | --------------------------- | ------------------ |
| Basic Auth        | `Test Basic Auth`           | `BASIC-001`        |
| OAuth / Bearer    | `Test OAuth Bearer`         | `OAUTH-002`        |
| X-API-Key         | `Test X-API-Key`            | `APIKEY-003`       |
| ApiKey Header     | `Test ApiKey Header`        | `APIKEY-004`       |
| API Key Query     | `Test API Key Query`        | `APIKEY-005`       |
| No Authentication | `Test No Authentication`    | `NOAUTH-006`       |
| ngrok Basic       | `Test Basic Auth - ngrok`   | `NGROK-BASIC-101`  |
| ngrok OAuth       | `Test OAuth Bearer - ngrok` | `NGROK-OAUTH-102`  |
| ngrok API Key     | `Test API Key - ngrok`      | `NGROK-APIKEY-103` |

---

# Sharing Logs With the Team

If the mock server is deployed to a shared environment, the team can access:

```text
https://<your-host>/logs
```

for the browser dashboard.

The JSON logs are available at:

```text
https://<your-host>/logs/json
```

For example:

```text
https://example.com/logs
```

The dashboard does not require a separate login in the current implementation.

> **Important:** This mock server is intended for testing. Do not expose real credentials, production payloads, or sensitive data through the public log dashboard.

# Deploying to Render.com

This mock server is configured and ready to be deployed as a **Web Service** on [Render](https://render.com/).

### Deployment Steps:

1. **Create a Web Service**:
   * Connect your GitHub repository containing this codebase to Render.
   * Select **Web Service** as the service type.

2. **Configure Service Settings**:
   * **Runtime**: `Python`
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `python mock_api.py` (The app launcher automatically detects Render's dynamic `$PORT` variable and disables hot reloading).

3. **Set Custom Credentials (Optional)**:
   * Under the **Environment** tab in your Render dashboard, add environment variables (e.g., `MOCK_API_KEY`, `MOCK_BASIC_USER`, `MOCK_BASIC_PASS`) to customize authentication secrets.

4. **Verify Live Console**:
   * Once deployed, navigate to `https://<your-subdomain>.onrender.com/logs` in your browser to view your live request log dashboard.

---

# Configuration Options (Environment Variables)

You can customize the credentials and logging thresholds by setting the following environment variables:

| Environment Variable | Description | Default Value |
| --- | --- | --- |
| `MOCK_BASIC_USER` | Expected username for Basic Authentication | `admin` |
| `MOCK_BASIC_PASS` | Expected password for Basic Authentication | `secretpassword` |
| `MOCK_API_KEY` | Expected API key value | `my-super-secret-api-key-123` |
| `MOCK_BEARER_TOKEN` | Expected OAuth / Bearer Token value | `oauth-token-xyz-789` |
| `MOCK_MAX_LOGS` | Maximum number of request logs kept in memory | `100` |

---

# Running Automated Tests

A comprehensive test suite is provided in the `tests/` directory to verify all routes and authentication logic.

To run the tests:

```bash
pytest -v
```

This will run tests on authentication endpoints, webhook multi-auth verification, and request logging.

---

# .gitignore

Recommended `.gitignore`:

```text
.venv/
__pycache__/
*.pyc
.env
```

---

# Quick Start

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

## 2. Start FastAPI

```bash
python mock_api.py
```

## 3. Open Swagger

```text
http://localhost:8000/docs
```

## 4. Open request logs

```text
http://localhost:8000/logs
```

## 5. Optional: expose the server through ngrok

Open another terminal:

```bash
ngrok http 8000
```

Your public webhook will be:

```text
https://<your-ngrok-url>/webhook
```

---

# Typical Test Flow

```text
                 ┌──────────────────────┐
                 │   Cloud Integration   │
                 └──────────┬───────────┘
                            │
                            │ HTTPS
                            ▼
                 ┌──────────────────────┐
                 │        ngrok         │
                 └──────────┬───────────┘
                            │
                            │ HTTP
                            ▼
                 ┌──────────────────────┐
                 │   FastAPI Mock API   │
                 │     localhost:8000   │
                 └──────────┬───────────┘
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
        /webhook          /logs       /logs/json
             │              │              │
             ▼              ▼              ▼
       Authentication   Dashboard       JSON Logs
       + Payload
```

The main purpose of the server is to allow a cloud integration to send a webhook and then provide an easy way to verify **exactly what was received, which authentication mechanism was used, and what payload was sent**.
