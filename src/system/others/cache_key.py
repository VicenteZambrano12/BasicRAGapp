"""Shared cache key helper for session-scoped resources."""

from src.utils.redis_funcs import get_cache_key


def build_cache_key(session_id: str, category: str, subject: str) -> str:
    """Build a normalized cache key for a session/category/subject tuple."""
    return get_cache_key(session_id, category, subject)
