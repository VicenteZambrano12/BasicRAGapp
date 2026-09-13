"""Caches the category/subject configuration and compiled graph instance per session."""

import json
import logging
from typing import Any, Dict, Optional

from src.utils.cache.redis_client import redis_client

logger = logging.getLogger(__name__)

CONFIG_TTL_SECONDS = 60 * 60 * 24  # 1 day

# Compiled LangGraph instances can't be serialized to Redis/fakeredis, so they
# only ever live in this process-local dict. graph_config_cache mirrors Redis
# entries for the home endpoint's cache-size diagnostics.
graph_config_cache: Dict[str, Dict[str, str]] = {}
graph_instance_cache: Dict[str, Any] = {}


def save_graph_config_to_cache(cache_key: str, category: str, subject: str) -> None:
    """Persist the category/subject configuration for a session cache key."""
    payload = {"category": category, "subject": subject}
    graph_config_cache[cache_key] = payload
    try:
        redis_client.setex(f"config:{cache_key}", CONFIG_TTL_SECONDS, json.dumps(payload))
    except Exception as exc:
        logger.warning(f"[CACHE] Failed to persist config to cache backend: {exc}")


def load_graph_config_from_cache(cache_key: str) -> Optional[Dict[str, str]]:
    """Load a previously saved category/subject configuration, if any."""
    if cache_key in graph_config_cache:
        return graph_config_cache[cache_key]

    try:
        raw = redis_client.get(f"config:{cache_key}")
        if raw:
            payload = json.loads(raw)
            graph_config_cache[cache_key] = payload
            return payload
    except Exception as exc:
        logger.warning(f"[CACHE] Failed to load config from cache backend: {exc}")

    return None


def get_or_create_graph(cache_key: str, category: str, subject: str):
    """Return the cached compiled graph for a session, rebuilding it if needed."""
    if cache_key in graph_instance_cache:
        return graph_instance_cache[cache_key]

    # Imported lazily to avoid a circular import (create_system depends on nothing here).
    from src.utils.create_system import create_system

    graph = create_system(subject=subject, community=category)
    graph_instance_cache[cache_key] = graph
    return graph
