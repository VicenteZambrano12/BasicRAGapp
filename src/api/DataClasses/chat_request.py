"""Request model for chat interactions with optional multimodal input."""

from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Payload for user chat requests including text and optional image input."""

    session_id: str = Field(..., description="Unique identifier for the session.")
    query: str = Field("", description="User's text query.")
    image: Optional[str] = Field(
        None,
        description=(
            "Image data. Can be: HTTPS URL, data URL, or raw base64."
        ),
    )
    image_type: str = Field(
        "url",
        description="Type of image data: 'url' for URLs or 'base64' for base64 data",
    )
    category: str = Field("Community", description="Category for the system/database.")
    subject: str = Field("General", description="Subject within the category.")
