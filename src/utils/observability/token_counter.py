"""Approximate token counting for request/response logging (not billing-accurate)."""

import logging
from functools import lru_cache
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_IMAGE_TOKEN_ESTIMATE = 258  # Flat estimate for a single low-detail image block.


class TokenCounter:
    """Best-effort token counter used only for diagnostic logging."""

    def __init__(self):
        try:
            import tiktoken

            self._encoding = tiktoken.get_encoding("cl100k_base")
        except Exception as exc:
            logger.warning(f"[TOKENS] tiktoken unavailable, falling back to word-count estimate: {exc}")
            self._encoding = None

    def count_text(self, text: str) -> int:
        if not text:
            return 0
        if self._encoding:
            return len(self._encoding.encode(text))
        return max(1, len(text.split()))

    def count_messages(self, messages: List[Any]) -> Dict[str, int]:
        total = 0
        for message in messages:
            content = getattr(message, "content", None)
            if content is None and isinstance(message, dict):
                content = message.get("content", "")
            total += self._count_content(content)
        return {"total": total}

    def _count_content(self, content: Any) -> int:
        if isinstance(content, str):
            return self.count_text(content)
        if isinstance(content, list):
            total = 0
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text":
                    total += self.count_text(block.get("text", ""))
                elif block.get("type") == "image_url":
                    total += _IMAGE_TOKEN_ESTIMATE
            return total
        return 0


@lru_cache(maxsize=1)
def get_token_counter() -> TokenCounter:
    """Return a process-wide cached token counter instance."""
    return TokenCounter()
