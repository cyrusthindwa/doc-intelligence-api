import time
from services.redis_client import redis_client

# Plan limits - requests allowed per 60-second window
PLAN_LIMITS = {
    "demo": 10,
    "starter": 60,
    "pro": 300,
}

async def check_rate_limit(api_key_id: str, plan: str = "demo") -> dict:
    """
    Sliding window rate limiter using Redis
    
    Key pattern: rate:{api_key_id}:{current_minute}
    Each key auto-expires after 60 seconds - no manual cleanup needed.
    
    returns dict with:
        allowed (bool), limit (int), remaining (int), reset_at (int)
    """
    limit = PLAN_LIMITS.get(plan, PLAN_LIMITS["demo"])
    
    # Bucket requests into 60-second windows based on current time
    current_window = int(time.time() // 60)
    redis_key = f"rate:{api_key_id}:{current_window}"
    
    # Increment the request count for this window
    current_count = await redis_client.incr(redis_key)
    
    # Set the key to expire after 60 seconds if it's newly created
    if current_count == 1:
        await redis_client.expire(redis_key, 60)
        
    reset_at = (current_window + 1) * 60 
    remaining = max(0, limit - current_count)
    allowed = current_count <= limit
    
    return {
        "allowed": allowed,
        "limit": limit,
        "remaining": remaining,
        "reset_at": reset_at,
        "retry_after": reset_at - int(time.time()) if not allowed else 0,
    }