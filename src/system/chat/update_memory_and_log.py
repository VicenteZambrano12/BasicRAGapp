"""Chat helper to update memory and emit token usage logs."""

import logging

from src.utils.cache import update_conversation_memory


logger = logging.getLogger(__name__)


def update_memory_and_log(
    token_counter,
    cache_key: str,
    memory_user_content: str,
    response_text: str,
    initial_input_tokens: int,
    total_steps: int,
) -> None:
    """Persist conversation memory and log request token summary."""
    if memory_user_content and response_text:
        try:
            update_conversation_memory(cache_key, memory_user_content, response_text)
            logger.debug("Conversation memory updated", extra={"event": "memory_updated"})
        except Exception:
            logger.error(
                "Failed to update conversation memory",
                exc_info=True,
                extra={"event": "memory_update_failed"},
            )

    response_tokens = token_counter.count_text(response_text) if response_text else 0

    logger.info(
        "Chat turn token usage",
        extra={
            "event": "token_usage",
            "input_tokens": initial_input_tokens,
            "response_tokens": response_tokens,
            "total_tokens": initial_input_tokens + response_tokens,
            "total_steps": total_steps,
        },
    )
