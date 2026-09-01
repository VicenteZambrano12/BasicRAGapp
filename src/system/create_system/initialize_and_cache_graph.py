"""Create-system helper that builds and caches a new graph instance."""

import logging
from src.utils.create_system import create_system
from src.utils.redis_funcs import graph_instance_cache, save_graph_config_to_cache


logger = logging.getLogger(__name__)


def initialize_and_cache_graph(cache_key: str, category: str, subject: str) -> None:
    """Initialize a new graph instance and persist its configuration."""
    logger.info("[CREATE_SYSTEM] Initializing graph...")
    graph = create_system(subject=subject, community=category)
    graph_instance_cache[cache_key] = graph
    save_graph_config_to_cache(cache_key, category, subject)
    logger.info("[CREATE_SYSTEM] Graph initialized successfully")
