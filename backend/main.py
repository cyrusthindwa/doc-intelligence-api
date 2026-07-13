from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Only load .env in local dev, not in Docker
if not os.getenv("DOCKER_ENV"):
    load_dotenv()

from routes.extract import router as extract_router
from routes.schema import router as schema_router
from routes.batch import router as batch_router
from routes.keys import router as keys_router
from services.redis_client import get_redis_connection
from middleware.auth import auth_middleware
from middleware.logging import logging_middleware
from database import engine, Base, AsyncSessionLocal
from services.auth_service import create_api_key
from sqlalchemy import select, func
from models.schemas import APIKey

app = FastAPI(
    title="AI Document Intelligence API",
    description="Extract structured data from any document using AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── Startup: auto-create tables & seed default API key ─────────
@app.on_event("startup")
async def startup():
    """Create tables if they don't exist and seed a default API key."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed a default demo key if no keys exist
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(func.count()).select_from(APIKey))
        count = result.scalar()
        if count == 0:
            await create_api_key(name="Default Demo Key", plan="demo", db=db)
            print("✅ Seeded default demo API key")

# ── Middleware (order matters — runs bottom to top on request) ────────────────
app.add_middleware(CORSMiddleware,
    allow_origins=[os.getenv("CORS_ORIGIN", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware using add_middleware for correct ordering
app.middleware("http")(logging_middleware)
app.middleware("http")(auth_middleware)


@app.middleware("http")
async def add_rate_limit_headers(request: Request, call_next):
    response = await call_next(request)
    if hasattr(request.state, "rate_limit"):
        rl = request.state.rate_limit
        response.headers["X-RateLimit-Limit"]     = str(rl["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rl["remaining"])
        response.headers["X-RateLimit-Reset"]     = str(rl["reset_at"])
    return response


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns the overall API health status, version, and the status of
    downstream services (Redis). Use this endpoint for monitoring and
    load-balancer health probes.

    ---
    Example request:
        GET /health

    Example response (200):
        {
            "status": "healthy",
            "version": "1.0.0",
            "services": {
                "redis": "operational"
            }
        }

    Example response when Redis is down (200):
        {
            "status": "healthy",
            "version": "1.0.0",
            "services": {
                "redis": "down"
            }
        }
    """
    redis_ok = await get_redis_connection()
    return {
        "status":  "healthy",
        "version": "1.0.0",
        "services": {
            "redis": "operational" if redis_ok else "down",
        }
    }


app.include_router(extract_router, prefix="/v1", tags=["Extraction"])
app.include_router(schema_router,  prefix="/v1", tags=["Schemas"])
app.include_router(batch_router,   prefix="/v1", tags=["Batch"])
app.include_router(keys_router,    prefix="/v1", tags=["Keys"])