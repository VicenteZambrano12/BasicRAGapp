"""Chat helper to execute graph streaming and collect AI response."""

import logging
import time
from typing import Any, Dict, List, Tuple

from fastapi import HTTPException


logger = logging.getLogger(__name__)


def run_graph_stream(graph: Any, chat_state: Dict[str, Any]) -> Tuple[str, int, List[Any]]:
    """Run the graph stream and return final response text, step count, and retrieved documents."""
    start_time = time.perf_counter()
    response_text = None
    total_steps = 0
    documents: List[Any] = []

    for step in graph.stream(chat_state, stream_mode="values"):
        total_steps += 1
        last_msg = step["messages"][-1]
        if last_msg.type == "ai":
            response_text = last_msg.content
        if step.get("documents"):
            documents = step["documents"]

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    if not response_text:
        logger.error(
            "Graph produced no assistant response",
            extra={
                "event": "graph_empty_response",
                "total_steps": total_steps,
                "duration_ms": duration_ms,
            },
        )
        raise HTTPException(status_code=500, detail="No response generated")

    logger.info(
        "Graph response generated",
        extra={
            "event": "graph_completed",
            "total_steps": total_steps,
            "response_chars": len(response_text),
            "documents_retrieved": len(documents),
            "duration_ms": duration_ms,
        },
    )
    return response_text, total_steps, documents
