import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from models.schemas import UsageLog


async def log_request(
    db: AsyncSession,
    api_key_id: str,
    endpoint: str,
    method: str,
    status_code: int,
    error_code: str = None,
    file_size_bytes: int = None,
    processing_ms: int = None,
    tokens_used: int = None,
    ip_address: str = None,
) -> None:
    """
    Write one row to usage_logs for every API request.
    Called after every request — success or failure.
    Never raises — a logging failure must never break the main request.
    """
    try:
        log = UsageLog(
            id=uuid.uuid4(),
            api_key_id=uuid.UUID(api_key_id),
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            error_code=error_code,
            file_size_bytes=file_size_bytes,
            processing_ms=processing_ms,
            tokens_used=tokens_used,
            ip_address=ip_address,
            request_id=str(uuid.uuid4()),
        )
        db.add(log)
        await db.commit()
    except Exception as e:
        # Log failure must never surface to the client
        print(f"[UsageLogger] Failed to write log: {e}")