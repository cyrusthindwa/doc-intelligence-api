import time
from fastapi import Request
from database import AsyncSessionLocal
from services.usage_logger import log_request


async def logging_middleware(request: Request, call_next):
    """
    Logs every API request to the usage_logs table after it completes.
    Captures: endpoint, method, status code, processing time, IP address.
    """
    start_time = time.time()

    response = await call_next(request)

    # Skip logging for non-API routes
    SKIP_PATHS = {"/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"}
    if request.url.path in SKIP_PATHS:
        return response

    processing_ms = int((time.time() - start_time) * 1000)
    status_code = response.status_code
    ip_address = request.client.host if request.client else None

    # Only log if we have an authenticated API key
    api_key = getattr(request.state, "api_key", None)
    if not api_key:
        return response

    # Write the log row asynchronously — never block the response
    try:
        async with AsyncSessionLocal() as db:
            await log_request(
                db=db,
                api_key_id=str(api_key.id),
                endpoint=request.url.path,
                method=request.method,
                status_code=status_code,
                processing_ms=processing_ms,
                ip_address=ip_address,
            )
    except Exception as e:
        print(f"[LoggingMiddleware] Failed to log request: {e}")

    return response