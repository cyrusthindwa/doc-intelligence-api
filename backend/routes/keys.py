import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from database import AsyncSessionLocal
from services.auth_service import create_api_key

router = APIRouter()

VALID_PLANS = {"demo", "starter", "pro"}


class CreateKeyRequest(BaseModel):
    name: str
    plan: str = "demo"


@router.post("/keys")
async def create_key(body: CreateKeyRequest):
    """
    Create a new API key.

    Generates a unique API key with the specified name and plan.
    The returned key is shown only once — save it immediately.
    The key's rate limit is determined by the plan:
      - demo:    10 requests/minute
      - starter: 60 requests/minute
      - pro:    300 requests/minute

    ---
    Example request:
        POST /v1/keys
        Content-Type: application/json

        {
            "name": "My Integration",
            "plan": "demo"
        }

    Example response (201):
        {
            "status": "success",
            "api_key": "doc_demo_a1b2c3d4e5f6...",
            "key_prefix": "doc_demo_",
            "name": "My Integration",
            "plan": "demo",
            "id": "a1b2c3d4-...-...-...-............",
            "warning": "Save this key immediately. It will not be shown again."
        }

    Example error — invalid plan (400):
        {
            "detail": "Invalid plan 'enterprise'. Valid plans: demo, starter, pro"
        }

    Example error — missing name (400):
        {
            "detail": "Key name is required."
        }
    """
    if body.plan not in VALID_PLANS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid plan '{body.plan}'. Valid plans: {', '.join(VALID_PLANS)}"
        )

    if not body.name or not body.name.strip():
        raise HTTPException(status_code=400, detail="Key name is required.")

    async with AsyncSessionLocal() as db:
        result = await create_api_key(
            name=body.name.strip(),
            plan=body.plan,
            db=db,
        )

    return JSONResponse(status_code=201, content={
        "status": "success",
        **result,
    })


@router.get("/keys/validate")
async def validate_key_endpoint():
    """
    Validate an API key.

    Confirms that the API key provided in the `x-api-key` header is
    active, not revoked, and has not expired. The auth middleware
    performs validation before this handler runs, so a 200 response
    guarantees the key is valid.

    ---
    Example request:
        GET /v1/keys/validate
        x-api-key: <your-api-key>

    Example response (200):
        {
            "status": "success",
            "message": "API key is valid."
        }

    Example error — missing/invalid key (403):
        {
            "status": "error",
            "error": {
                "code": "INVALID_API_KEY",
                "message": "API key is invalid, expired, or has been revoked.",
                "detail": "Check your key or contact support."
            }
        }
    """
    return JSONResponse(status_code=200, content={
        "status":  "success",
        "message": "API key is valid.",
    })