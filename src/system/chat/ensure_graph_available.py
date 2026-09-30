"""Chat helper to validate initialization and retrieve graph instance."""

import logging
from fastapi import HTTPException

from src.utils.cache import get_or_create_graph, load_graph_config_from_cache


logger = logging.getLogger(__name__)


def ensure_graph_available(cache_key: str, category: str, subject: str):
    """Ensure graph is initialized and return a ready-to-use graph instance."""
    cached_config = load_graph_config_from_cache(cache_key)
    if not cached_config:
        logger.warning(
            "Chat requested before system initialization",
            extra={
                "event": "graph_not_initialized",
                "category": category,
                "subject": subject,
            },
        )
        raise HTTPException(
            status_code=400,
            detail=f"System not initialized for '{category}-{subject}'. Call /create_system first.",
        )

    try:
        graph = get_or_create_graph(cache_key, category, subject)
        logger.debug(
            "Graph loaded from cache",
            extra={"event": "graph_loaded", "category": category, "subject": subject},
        )
        return graph
    except Exception as exc:
        logger.error(
            "Failed to initialize graph",
            exc_info=True,
            extra={
                "event": "graph_initialization_failed",
                "category": category,
                "subject": subject,
            },
        )
        raise HTTPException(status_code=500, detail=f"Failed to initialize graph: {exc}")
