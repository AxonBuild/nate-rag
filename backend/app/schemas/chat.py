from typing import Any, Optional

from pydantic import BaseModel, Field


class ChatMessageSchema(BaseModel):
    role: str
    content: str


class ChatRequestSchema(BaseModel):
    question: str
    conversation_id: Optional[str] = None
    chat_history: Optional[list[ChatMessageSchema]] = None
    topic: Optional[str] = None
    doc_type: Optional[str] = None
    system_prompt: Optional[str] = None
    retrieval_limit: Optional[int] = Field(default=None, ge=5, le=20)


class ChatResponseSchema(BaseModel):
    answer: str
    search: dict[str, Any]
    timing: dict[str, Any]
    verification: Optional[dict[str, Any]] = None
