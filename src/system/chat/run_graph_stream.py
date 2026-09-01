"""Chat helper to execute graph streaming and collect AI response."""

import logging
from typing import Any, Dict, Tuple

from fastapi import HTTPException


logger = logging.getLogger(__name__)


def run_graph_stream(graph: Any, chat_state: Dict[str, Any]) -> Tuple[str, int]:
    """Run the graph stream and return final response text and step count."""
    logger.info("[CHAT] Processing request through graph...")
    response_text = None
    total_steps = 0

    for step in graph.stream(chat_state, stream_mode="values"):
        total_steps += 1
        last_msg = step["messages"][-1]
        if last_msg.type == "ai":
            response_text = last_msg.content

    if not response_text:
        logger.error("[CHAT] No response generated from graph")
        raise HTTPException(status_code=500, detail="No response generated")

    logger.info(f"[CHAT] Response generated successfully ({len(response_text)} chars)")
    return response_text, total_steps
