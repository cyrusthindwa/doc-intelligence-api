import os 
import redis.asyncio as redis
from dotenv import load_dotenv

# Only load .env in local dev, not in Docker
if not os.getenv("DOCKER_ENV"):
    load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Single shared connection pool - reused across the whole app
redis_client = redis.from_url(
    REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)

async def get_redis_connection() -> bool:
    """Used by /health to confirm Redis is reachable"""
    try:
        await redis_client.ping()
        return True
    except Exception:
        return False