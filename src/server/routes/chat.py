"""Chat API route."""
import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

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
    retrieval_limit: Optional[int] = Field(default=None, ge=5, le=20)


class ChatResponse(BaseModel):
    answer: str
    search: dict[str, Any]
    timing: dict[str, Any]
    verification: Optional[dict[str, Any]] = None


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: SearchService = Depends(get_search_service),
):
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    try:
        history = [{"role": m.role, "content": m.content} for m in (request.chat_history or [])]
        logger.info(
            "[chat] POST /chat/ history=%d retrieval_limit=%s",
            len(history),
            request.retrieval_limit,
        )
        result = await service.chat(
            question=request.question,
            chat_history=history or None,
            topic=request.topic,
            doc_type=request.doc_type,
            system_prompt_override=request.system_prompt,
            retrieval_limit=request.retrieval_limit,
        )
        return ChatResponse(
            answer=result["answer"],
            search=result["search"],
            timing=result["timing"],
            verification=result.get("verification"),
        )
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _sse_message(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    service: SearchService = Depends(get_search_service),
):
    """SSE stream: status events, then done with full verified answer."""
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    async def event_generator():
        history = [{"role": m.role, "content": m.content} for m in (request.chat_history or [])]
        logger.info(
            "[chat] POST /chat/stream history=%d retrieval_limit=%s",
            len(history),
            request.retrieval_limit,
        )
        try:
            async for item in service.chat_stream(
                question=request.question,
                chat_history=history or None,
                topic=request.topic,
                doc_type=request.doc_type,
                system_prompt_override=request.system_prompt,
                retrieval_limit=request.retrieval_limit,
            ):
                if item["event"] == "status":
                    logger.info("[chat] sse status phase=%s", item["data"].get("phase"))
                elif item["event"] == "done":
                    logger.info("[chat] sse done answer_chars=%d", len(item["data"].get("answer") or ""))
                elif item["event"] == "error":
                    logger.error("[chat] sse error %s", item["data"].get("message"))
                yield _sse_message(item["event"], item["data"])
        except Exception as e:
            logger.error("[chat] stream route error: %s", e, exc_info=True)
            yield _sse_message("error", {"message": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
