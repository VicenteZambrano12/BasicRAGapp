"""Chat helper to validate initialization and retrieve graph instance."""

import logging
from fastapi import HTTPException

from src.utils.redis_funcs import get_or_create_graph, load_graph_config_from_cache


logger = logging.getLogger(__name__)


def ensure_graph_available(cache_key: str, category: str, subject: str):
    """Ensure graph is initialized and return a ready-to-use graph instance."""
    cached_config = load_graph_config_from_cache(cache_key)
    if not cached_config:
        logger.error(f"[CHAT] System not initialized for '{category}-{subject}'")
        raise HTTPException(
            status_code=400,
            detail=f"System not initialized for '{category}-{subject}'. Call /create_system first.",
        )

    try:
        logger.info("[CHAT] Loading graph from cache...")
        graph = get_or_create_graph(cache_key, category, subject)
        logger.info("[CHAT] Graph loaded successfully")
        return graph
    except Exception as exc:
        logger.error(f"[CHAT] Failed to initialize graph: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to initialize graph: {exc}")
