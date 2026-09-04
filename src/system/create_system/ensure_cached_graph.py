"""Create-system helper that ensures an existing cached graph is loaded."""

from src.utils.redis_funcs import get_or_create_graph


def ensure_cached_graph(cache_key: str, category: str, subject: str) -> None:
    """Load a graph into instance cache when configuration already exists."""
    get_or_create_graph(cache_key, category, subject)
