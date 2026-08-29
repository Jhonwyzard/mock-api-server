import secrets
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBasicCredentials

from ..config import settings
from ..core.security import basic_security, bearer_security

router = APIRouter(tags=["Authentication"])


@router.get("/basic/auth")
async def basic_auth(
    credentials: HTTPBasicCredentials = Depends(basic_security),
):
    """
    Test Basic Authentication.

    Swagger:
        Click Authorize and enter the username/password.
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing Basic Authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    valid_username = secrets.compare_digest(
        credentials.username,
        settings.VALID_BASIC_USER,
    )
    valid_password = secrets.compare_digest(
        credentials.password,
        settings.VALID_BASIC_PASS,
    )

    if not valid_username or not valid_password:
        raise HTTPException(
            status_code=401,
            detail="Invalid Basic Auth credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return {
        "status": "success",
        "message": "Basic Authentication successful",
        "username": credentials.username,
    }


@router.get("/oauth/protected")
async def oauth_protected(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_security),
):
    """
    Test OAuth Bearer Token authentication.

    Swagger:
        Click Authorize and enter the Bearer token.
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing Bearer Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    if not secrets.compare_digest(token, settings.VALID_BEARER_TOKEN):
        raise HTTPException(
            status_code=401,
            detail="Invalid Bearer Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "status": "success",
        "message": "OAuth Bearer Token is valid",
    }
