"""Minimal chat-model interface backed by the self-deployed Vertex vision endpoint.

Flattens a LangChain message list into Llama 3.2's raw chat prompt format so the
same `.invoke(messages) -> AIMessage` contract used by ChatGoogleGenerativeAI can
be swapped in for the self-deployed model.
"""

from typing import List, Optional

from langchain_core.messages import AIMessage, BaseMessage

from src.utils.chat.vertex_vision_endpoint import vertex_generate
from src.utils.create_system.state import extract_query_text

_ROLE_MAP = {"system": "system", "human": "user", "ai": "assistant"}


def _last_image_url(messages: List[BaseMessage]) -> Optional[str]:
    for message in reversed(messages):
        content = getattr(message, "content", None)
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "image_url":
                    return block.get("image_url", {}).get("url")
    return None


def _build_prompt(messages: List[BaseMessage]) -> str:
    parts = ["<|begin_of_text|>"]
    for message in messages:
        role = _ROLE_MAP.get(getattr(message, "type", ""), "user")
        text = extract_query_text(message)
        parts.append(f"<|start_header_id|>{role}<|end_header_id|>\n\n{text}<|eot_id|>")
    parts.append("<|start_header_id|>assistant<|end_header_id|>\n\n")
    return "".join(parts)


class VertexSelfDeployedLLM:
    """`.invoke(messages)` chat interface backed by the self-deployed Llama endpoint."""

    def invoke(self, messages: List[BaseMessage]) -> AIMessage:
        image_url = _last_image_url(messages)
        prompt = _build_prompt(messages)
        if image_url:
            prompt = f"<|image|>{prompt}"
        text = vertex_generate(prompt, image_url=image_url, max_tokens=512)
        return AIMessage(content=text)
