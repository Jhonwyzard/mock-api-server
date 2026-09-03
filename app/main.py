from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import auth, webhook, logs

app = FastAPI(
    title="API Mock Server",
    description="Generic API mock server for authentication and webhook testing",
    version="1.0.0",
)

# Enable CORS for cross-origin frontend integration testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register routes from our modular routers
app.include_router(auth.router)
app.include_router(webhook.router)
app.include_router(logs.router)


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
            "webhook": "POST /webhook or /webhook/*",
            "logs": "GET /logs",
            "logs_json": "GET /logs/json",
            "clear_logs": "DELETE /logs",
            "websocket": "WS /logs/ws",
            "swagger": "GET /docs",
        },
    }
