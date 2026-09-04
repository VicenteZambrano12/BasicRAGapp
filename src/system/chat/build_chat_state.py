"""Chat helper to compose graph input state from memory and current content."""

from typing import Dict, Any, List


def build_chat_state(
    message_content: List[Dict[str, Any]],
    intermediate_memory: str,
    memory_summary: str,
    recent_turns: List[Dict[str, str]],
    language_instruction: str = "Responde siempre en español.",
) -> Dict[str, Any]:
    """Construct graph state including visual context, summary, and recent turns."""
    chat_state = {"messages": []}

    chat_state["messages"].append(
        {"role": "system", "content": language_instruction}
    )

    if intermediate_memory:
        chat_state["messages"].append(
            {"role": "system", "content": f"Visual context extracted: {intermediate_memory}"}
        )

    if memory_summary:
        chat_state["messages"].append(
            {"role": "system", "content": f"Previous context summary: {memory_summary}"}
        )

    for turn in recent_turns:
        chat_state["messages"].append({"role": "user", "content": turn["user"]})
        chat_state["messages"].append({"role": "assistant", "content": turn["ai"]})

    chat_state["messages"].append({"role": "user", "content": message_content})
    return chat_state
