"""Chat helper to update memory and emit token usage logs."""

import logging

from src.utils.summary_func import update_conversation_memory


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
            logger.info("[CHAT] Memory updated")
        except Exception as mem_error:
            logger.error(f"[CHAT] Failed to update memory: {mem_error}")

    response_tokens = token_counter.count_text(response_text) if response_text else 0

    logger.info("[TOKEN COUNT] ========== REQUEST SUMMARY ==========")
    logger.info(f"[TOKEN COUNT] Initial input: {initial_input_tokens} tokens")
    logger.info(f"[TOKEN COUNT] Total steps: {total_steps}")
    logger.info(f"[TOKEN COUNT] Response: {response_tokens} tokens")
    logger.info("[TOKEN COUNT] =====================================")
