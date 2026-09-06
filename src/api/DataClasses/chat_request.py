"""Request model for chat interactions with optional multimodal input."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Payload for user chat requests including text and optional image input."""

    session_id: str = Field(..., description="Unique identifier for the session.")
    query: str = Field("", description="User's text query.")
    image: Optional[str] = Field(
        None,
        description="Image data as an HTTPS URL, data URL, or raw base64 string.",
    )
    image_type: str = Field(
        "url",
        description="Image encoding type: 'url' or 'base64'.",
    )
    category: str = Field(
        "Community", description="Category used to select the study system."
    )
    subject: str = Field("General", description="Subject within the category.")
    language: Literal["ES", "EN"] = Field(
        "ES", description="Language for the assistant response."
    )
