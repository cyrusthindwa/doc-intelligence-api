from fastapi import Request, HTTPException
from services.rate_limiter import check_rate_limit


async def enforce_rate_limit(request: Request):
    """
    Rate limits by real API key ID now that auth middleware runs first.
    Falls back to IP address if no API key is present (shouldn't happen
    after auth middleware, but defensive coding is good practice).
    """
    api_key = getattr(request.state, "api_key", None)

    if api_key:
        # Use real key ID and plan from the database
        client_id = str(api_key.id)
        plan = api_key.plan
    else:
        # Fallback — should not reach here after auth middleware
        client_id = request.client.host if request.client else "unknown"
        plan = "demo"

    result = await check_rate_limit(api_key_id=client_id, plan=plan)

    request.state.rate_limit = result

    if not result["allowed"]:
        raise HTTPException(
            status_code=429,
            detail={
                "status": "error",
                "error": {
                    "code":    "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit of {result['limit']} requests per minute exceeded.",
                    "detail":  f"Retry after {result['retry_after']} seconds.",
                }
            },
            headers={"Retry-After": str(result["retry_after"])}
        )