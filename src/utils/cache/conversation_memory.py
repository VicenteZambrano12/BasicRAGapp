"""Rolling conversation memory: recent turns plus a rolling text summary."""

import json
import logging

from src.utils.cache.session_memory import get_str_field_from_cache, set_str_field_to_cache

logger = logging.getLogger(__name__)

MAX_RECENT_TURNS = 6
MAX_SUMMARY_CHARS = 2000


def update_conversation_memory(cache_key: str, user_content: str, response_text: str) -> None:
    """Append the latest turn to memory, folding overflow turns into a rolling summary."""
    raw = get_str_field_from_cache(cache_key)
    summary = ""
    recent = []

    if raw:
        try:
            data = json.loads(raw)
            summary = data.get("summary", "")
            recent = data.get("recent", [])
        except json.JSONDecodeError:
            logger.warning("[MEMORY] Failed to parse existing memory JSON; resetting")

    recent.append({"user": user_content, "ai": response_text})

    while len(recent) > MAX_RECENT_TURNS:
        oldest = recent.pop(0)
        summary = f"{summary}\nQ: {oldest['user'][:150]} | A: {oldest['ai'][:150]}".strip()

    if len(summary) > MAX_SUMMARY_CHARS:
        summary = summary[-MAX_SUMMARY_CHARS:]

    set_str_field_to_cache(cache_key, json.dumps({"summary": summary, "recent": recent}))
