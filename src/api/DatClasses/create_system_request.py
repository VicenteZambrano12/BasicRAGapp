from pydantic import BaseModel, Field


class CreateSystemRequest(BaseModel):
    session_id: str = Field(..., description="Unique identifier for the session.")
    category: str = Field("Community", description="Category for the system/database.")
    subject: str = Field("General", description="Subject within the category.")
