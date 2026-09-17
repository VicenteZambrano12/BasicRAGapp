"""Chat endpoint with text/image handling, memory loading, and graph execution."""

from fastapi import APIRouter

from src.api.DataClasses.chat_request import ChatRequest
from src.api.DataClasses.chat_response import ChatResponse
from src.system.chat.chat import execute_chat


router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a chat message",
    description=(
        "Process a text or image-assisted chat message using the session's "
        "configured study system."
    ),
    response_description="Assistant response and source documents for the submitted chat turn.",
)
async def chat(data: ChatRequest) -> ChatResponse:
    """Process a chat turn and return the assistant response text and sources."""
    return execute_chat(data)
