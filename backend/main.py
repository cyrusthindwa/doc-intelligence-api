from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

from routes.extract import router as extract_router
from routes.schema import router as schema_router
from routes.batch import router as batch_router
from services.redis_client import get_redis_connection

app = FastAPI(
    title="AI Doc Intelligence API",
    description="Extract structured data from documents using AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ORIGIN","http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_rate_limit_headers(request: Request, call_next):
    response = await call_next(request)
    
    # If  the rate limit dependency ran, attach its info as headers
    if hasattr(request.state, "rate_limit"):
        rl = request.state.rate_limit
        response.headers["X-RateLimit-Limit"] = str(rl["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rl["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rl["reset_at"])
        
    return response

@app.get("/health")
async def health_check():
    redis_ok = await get_redis_connection()
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "redis": "operational" if redis_ok else "down"
        }
    }
    
# Register routes
app.include_router(extract_router, prefix="/v1", tags=["Extraction"])
app.include_router(schema_router, prefix="/v1", tags=["Schemas"])
app.include_router(batch_router, prefix="/v1", tags=["Batch"])