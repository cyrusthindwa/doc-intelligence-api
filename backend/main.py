from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

from routes.extract import router as extract_router

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

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0"
    }
    
# Register routes
app.include_router(extract_router, prefix="/v1", tags=["Extraction"])