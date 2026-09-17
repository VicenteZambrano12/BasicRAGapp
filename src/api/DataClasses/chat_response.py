"""Response model for chat interactions, including retrieved source documents."""

from typing import List, Optional
from pydantic import BaseModel, Field


class SourceDoc(BaseModel):
    """A single source document referenced by the assistant's answer."""

    doc_id: str = Field(..., description="Stable identifier for the source document (relative path).")
    file_name: str = Field(..., description="Original file name of the source document.")
    page: Optional[int] = Field(None, description="1-indexed page the retrieved chunk came from.")
    url: str = Field(..., description="Openable URL for the document (signed, time-limited).")


class ChatResponse(BaseModel):
    """Payload returned to the client for a chat turn."""

    response: Optional[str] = Field(None, description="Assistant response text.")
    sources: List[SourceDoc] = Field(default_factory=list, description="Documents backing the answer.")
