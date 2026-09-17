"""Redis connection setup, shared by every cache module in this package.

Uses a real Redis server when REDIS_HOST/REDIS_URL is configured and reachable.
Otherwise (local dev without Redis, or a cloud deploy where Redis isn't wired up
yet) it transparently falls back to fakeredis: an in-memory, non-persistent
simulation of the Redis API, so the exact same read/write code path runs in both
environments and cache entries don't survive a process restart either way.
"""

import logging
import os

logger = logging.getLogger(__name__)

REDIS_ENABLED = False  # True only when backed by a real Redis server (not fakeredis)


def _connect_real_redis():
    """Connect to a real Redis server if REDIS_URL/REDIS_HOST is configured and reachable."""
    import redis as redis_lib

    redis_url = (os.getenv("REDIS_URL") or "").strip()
    redis_host = (os.getenv("REDIS_HOST") or "").strip()

    if not redis_url and not redis_host:
        return None

    client = (
        redis_lib.from_url(redis_url, decode_responses=True)
        if redis_url
        else redis_lib.Redis(
            host=redis_host,
            port=int(os.getenv("REDIS_PORT", "6379")),
            decode_responses=True,
        )
    )
    client.ping()
    return client


try:
    redis_client = _connect_real_redis()
except Exception as exc:
    logger.warning(f"[CACHE] Real Redis unreachable, falling back to fakeredis: {exc}")
    redis_client = None

if redis_client is not None:
    REDIS_ENABLED = True
    logger.info("[CACHE] Connected to real Redis")
else:
    import fakeredis

    redis_client = fakeredis.FakeStrictRedis(decode_responses=True)
    logger.info("[CACHE] REDIS_HOST/REDIS_URL not set or unreachable; using fakeredis (non-persistent)")


def get_cache_key(session_id: str, category: str, subject: str) -> str:
    """Build a normalized cache key for a session/category/subject tuple."""
    return f"{session_id}:{category}:{subject}"
