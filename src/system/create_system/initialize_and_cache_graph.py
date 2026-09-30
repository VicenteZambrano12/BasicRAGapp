"""Create-system helper that builds and caches a new graph instance."""

import logging
import time

from src.utils.cache import graph_instance_cache, save_graph_config_to_cache
from src.utils.create_system import create_system


logger = logging.getLogger(__name__)


def initialize_and_cache_graph(cache_key: str, category: str, subject: str) -> None:
    """Initialize a new graph instance and persist its configuration."""
    start_time = time.perf_counter()
    graph = create_system(subject=subject, community=category)
    graph_instance_cache[cache_key] = graph
    save_graph_config_to_cache(cache_key, category, subject)
    logger.info(
        "Graph initialized and cached",
        extra={
            "event": "graph_initialized",
            "category": category,
            "subject": subject,
            "duration_ms": round((time.perf_counter() - start_time) * 1000, 2),
        },
    )
