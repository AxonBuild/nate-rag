from typing import Any, Optional

from pydantic import BaseModel, Field


class ConversationCreateSchema(BaseModel):
    title: str = Field(default="New conversation", max_length=500)


class ConversationSummarySchema(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class MessageOutSchema(BaseModel):
    id: str
    role: str
    content: str
    created_at: str
    metadata: Optional[dict[str, Any]] = None


class ConversationDetailSchema(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: list[MessageOutSchema]
