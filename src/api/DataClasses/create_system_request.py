"""Request model for creating or loading a session-specific RAG system."""

from typing import Literal

from pydantic import BaseModel, Field


class CreateSystemRequest(BaseModel):
    """Payload required to initialize a graph for a session/category/subject."""

    session_id: str = Field(..., description="Unique identifier for the session.")
    category: str = Field("Community", description="Category for the system/database.")
    subject: str = Field("General", description="Subject within the category.")
    language: Literal["ES", "EN"] = Field(
        "ES", description="Language for the assistant response."
    )
