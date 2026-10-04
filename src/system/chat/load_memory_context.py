"""Chat helper to load summary and recent turns from cache."""

import json
import logging
from typing import List, Dict, Tuple

from src.utils.cache import get_str_field_from_cache


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
            logger.debug(
                "Conversation memory loaded",
                extra={
                    "event": "memory_loaded",
                    "recent_turns": len(recent_turns),
                    "has_summary": bool(memory_summary),
                },
            )
        except json.JSONDecodeError:
            logger.warning(
                "Failed to parse cached conversation memory, starting fresh",
                extra={"event": "memory_parse_failed"},
            )

    return memory_summary, recent_turns
