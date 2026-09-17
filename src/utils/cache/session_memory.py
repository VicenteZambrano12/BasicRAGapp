"""Raw string storage for a session's conversation-memory JSON blob."""

import logging
from typing import Optional

from src.utils.cache.redis_client import redis_client

logger = logging.getLogger(__name__)

MEMORY_TTL_SECONDS = 60 * 60 * 6  # 6 hours


def get_str_field_from_cache(cache_key: str) -> Optional[str]:
    """Return the raw conversation-memory JSON string for a session, if any."""
    try:
        return redis_client.get(f"memory:{cache_key}")
    except Exception as exc:
        logger.warning(f"[CACHE] Failed to load memory from cache backend: {exc}")
        return None


def set_str_field_to_cache(cache_key: str, value: str) -> None:
    """Persist the raw conversation-memory JSON string for a session."""
    try:
        redis_client.setex(f"memory:{cache_key}", MEMORY_TTL_SECONDS, value)
    except Exception as exc:
        logger.warning(f"[CACHE] Failed to persist memory to cache backend: {exc}")
