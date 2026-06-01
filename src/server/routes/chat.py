"""Chat API route."""
import logging
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.retrieval.search_service import SearchService
from src.server.dependencies import get_search_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str
    chat_history: Optional[list[ChatMessage]] = None
    topic: Optional[str] = None
    doc_type: Optional[str] = None
    system_prompt: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    search: dict[str, Any]
    timing: dict[str, Any]


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: SearchService = Depends(get_search_service),
):
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    try:
        history = [{"role": m.role, "content": m.content} for m in (request.chat_history or [])]
        result = await service.chat(
            question=request.question,
            chat_history=history or None,
            topic=request.topic,
            doc_type=request.doc_type,
            system_prompt_override=request.system_prompt,
        )
        return ChatResponse(
            answer=result["answer"],
            search=result["search"],
            timing=result["timing"],
        )
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
