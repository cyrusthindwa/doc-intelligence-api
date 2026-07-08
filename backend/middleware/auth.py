from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from database import AsyncSessionLocal
from services.auth_service import validate_api_key


async def auth_middleware(request: Request, call_next):
    """
    Checks every request for a valid API key in the x-api-key header.

    Public routes that skip auth:
    - GET /health
    - GET /docs
    - GET /redoc
    - GET /openapi.json
    """

    # Routes that do not require authentication
    PUBLIC_PATHS = {"/health", "/docs", "/redoc", "/openapi.json", "/v1/keys"}

    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    # Extract API key from header
    raw_key = request.headers.get("x-api-key", "").strip()

    if not raw_key:
        return JSONResponse(
            status_code=401,
            content={
                "status": "error",
                "error": {
                    "code":    "MISSING_API_KEY",
                    "message": "Authentication required.",
                    "detail":  "Include your API key in the x-api-key header.",
                }
            }
        )

    # Validate key against database
    async with AsyncSessionLocal() as db:
        api_key = await validate_api_key(raw_key, db)

    if not api_key:
        return JSONResponse(
            status_code=403,
            content={
                "status": "error",
                "error": {
                    "code":    "INVALID_API_KEY",
                    "message": "API key is invalid, expired, or has been revoked.",
                    "detail":  "Check your key or contact support.",
                }
            }
        )

    # Attach the validated key to request state
    # Routes and dependencies can now read request.state.api_key
    request.state.api_key = api_key

    return await call_next(request)