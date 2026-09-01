"""Chat helper to load summary and recent turns from cache."""

import json
import logging
from typing import List, Dict, Tuple

from src.utils.redis_funcs import get_str_field_from_cache


logger = logging.getLogger(__name__)


def load_memory_context(cache_key: str) -> Tuple[str, List[Dict[str, str]]]:
    """Load conversation summary and recent turns for a session cache key."""
    memory_json = get_str_field_from_cache(cache_key)
    memory_summary = ""
    recent_turns: List[Dict[str, str]] = []

    if memory_json:
        try:
            memory_data = json.loads(memory_json)
            memory_summary = memory_data.get("summary", "")
            recent_turns = memory_data.get("recent", [])
            logger.info(f"[CHAT] Loaded memory: {len(recent_turns)} recent turns")
        except json.JSONDecodeError:
            logger.warning("[CHAT] Failed to parse memory JSON")

    return memory_summary, recent_turns
