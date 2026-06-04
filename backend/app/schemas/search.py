from typing import Any, Optional

from pydantic import BaseModel, Field


class SearchMessageSchema(BaseModel):
    role: str
    content: str


class SearchRequestSchema(BaseModel):
    query: str
    chat_history: Optional[list[SearchMessageSchema]] = None
    topic: Optional[str] = None
    doc_type: Optional[str] = None
    retrieval_limit: Optional[int] = Field(default=None, ge=5, le=20)


class SearchResponseSchema(BaseModel):
    query: str
    refined_query: str
    keywords: list[str]
    results: list[dict[str, Any]]
    total_results: int
    timing: dict[str, Any]
