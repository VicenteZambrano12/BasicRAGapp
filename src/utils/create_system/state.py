"""Chat graph state definition shared by the retrieve/generate nodes."""

from typing import Annotated

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class GraphState(TypedDict):
    """Chat graph state: LangChain message history plus the last retrieved chunks."""

    messages: Annotated[list, add_messages]
    documents: list


def extract_query_text(message) -> str:
    """Extract plain text from a (possibly multimodal) message's content."""
    if message is None:
        return ""
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
        return " ".join(p for p in parts if p)
    return ""
