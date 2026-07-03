from fastapi import Request, HTTPException
from services.rate_limiter import check_rate_limit


async def enforce_rate_limit(request: Request):
    """
    FastAPI dependency — checks rate limit before the route runs.

    For now, uses the client's IP as the identifier since full API key
    auth lands on Day 14. This will be swapped to use api_key_id once
    auth middleware exists.
    """
    # Temporary identifier — IP address. Day 14 replaces this with api_key_id.
    client_id = request.client.host if request.client else "unknown"

    result = await check_rate_limit(api_key_id=client_id, plan="demo")

    # Attach rate limit info to request state so routes can read it
    request.state.rate_limit = result

    if not result["allowed"]:
        raise HTTPException(
            status_code=429,
            detail={
                "status": "error",
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit of {result['limit']} requests per minute exceeded.",
                    "detail": f"Retry after {result['retry_after']} seconds.",
                }
            },
            headers={"Retry-After": str(result["retry_after"])}
        )