import hashlib
import secrets
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.sql import func
from models.schemas import APIKey


def generate_api_key() -> tuple[str, str, str]:
    """
    Generate a new API key.
    Returns (raw_key, key_hash, key_prefix).

    The raw key is shown ONCE at creation and never stored.
    Only the hash is stored in the database.
    """
    # Generate 32 random bytes → 64 hex char key
    raw_key = f"sk_live_{secrets.token_hex(32)}"
    key_hash = hash_api_key(raw_key)
    key_prefix = raw_key[:8]  # "sk_live_" — shown in UI for identification

    return raw_key, key_hash, key_prefix


def hash_api_key(raw_key: str) -> str:
    """SHA-256 hash of the raw key. This is what gets stored."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


async def validate_api_key(
    raw_key: str,
    db: AsyncSession,
) -> APIKey | None:
    """
    Look up an API key by its hash.
    Returns the APIKey model if valid and active, None otherwise.
    Updates last_used_at on successful lookup.
    """
    if not raw_key:
        return None

    key_hash = hash_api_key(raw_key)

    result = await db.execute(
        select(APIKey).where(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True,
            APIKey.revoked_at == None,
        )
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        return None

    # Update last_used_at — non-blocking, fire and forget style
    await db.execute(
        update(APIKey)
        .where(APIKey.id == api_key.id)
        .values(last_used_at=func.now())
    )
    await db.commit()

    return api_key


async def create_api_key(
    name: str,
    plan: str,
    db: AsyncSession,
) -> dict:
    """
    Create and persist a new API key.
    Returns the raw key (shown once only) and metadata.
    """
    raw_key, key_hash, key_prefix = generate_api_key()

    new_key = APIKey(
        id=uuid.uuid4(),
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=name,
        plan=plan,
        rate_limit={"demo": 10, "starter": 60, "pro": 300}.get(plan, 10),
        is_active=True,
    )
    db.add(new_key)
    await db.commit()

    return {
        "api_key":    raw_key,     # shown ONCE — client must save this
        "key_prefix": key_prefix,
        "name":       name,
        "plan":       plan,
        "id":         str(new_key.id),
        "warning":    "Save this key immediately. It will not be shown again.",
    }