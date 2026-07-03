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
    In production this would require admin authentication.
    For now it is open so you can create keys for testing.
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
    Simple endpoint to confirm the caller's API key is valid.
    Auth middleware has already validated it before this runs.
    Useful for clients to test their key is working.
    """
    return JSONResponse(status_code=200, content={
        "status":  "success",
        "message": "API key is valid.",
    })