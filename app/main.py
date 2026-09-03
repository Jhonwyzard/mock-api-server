from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .core.rate_limiter import rate_limiter
from .routers import auth, logs, webhook

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


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Global sliding window rate limiting per IP address to protect against bombardment."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    limit = getattr(settings, "RATE_LIMIT_PER_SEC", 10)

    if not rate_limiter.is_allowed(client_ip=client_ip, limit=limit, window_seconds=1.0):
        return JSONResponse(
            status_code=429,
            content={
                "status": "error",
                "message": "Too Many Requests - Rate limit exceeded",
                "rate_limit_per_sec": limit,
            },
            headers={"Retry-After": "1"},
        )

    return await call_next(request)


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
