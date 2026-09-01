"""Chat helper to build multimodal message content from user input."""

from typing import List, Dict, Any, Tuple


def build_message_content(query: str) -> Tuple[List[Dict[str, Any]], str]:
    """Build base message content list and initial memory from text query."""
    message_content: List[Dict[str, Any]] = []
    intermediate_memory = ""

    if query:
        message_content.append({"type": "text", "text": query})
        intermediate_memory = f"Q: {query[:100]}"

    return message_content, intermediate_memory
