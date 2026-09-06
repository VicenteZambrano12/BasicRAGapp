"""Chat endpoint with text/image handling, memory loading, and graph execution."""

from typing import Dict, Optional

from fastapi import APIRouter

from src.api.DataClasses.chat_request import ChatRequest
from src.system.chat.chat import execute_chat


router = APIRouter()


@router.post(
    "/chat",
    response_model=Dict[str, Optional[str]],
    summary="Send a chat message",
    description=(
        "Process a text or image-assisted chat message using the session's "
        "configured study system."
    ),
    response_description="Assistant response for the submitted chat turn.",
)
async def chat(data: ChatRequest) -> Dict[str, Optional[str]]:
    """Process a chat turn and return the assistant response text."""
    return execute_chat(data)
