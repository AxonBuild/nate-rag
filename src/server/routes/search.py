"""Search API route."""
import logging
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.retrieval.search_service import SearchService
from src.server.dependencies import get_search_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search"])


class SearchMessage(BaseModel):
    role: str
    content: str


class SearchRequest(BaseModel):
    query: str
    chat_history: Optional[list[SearchMessage]] = None
    topic: Optional[str] = None
    doc_type: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    refined_query: str
    keywords: list[str]
    results: list[dict[str, Any]]
    total_results: int
    timing: dict[str, Any]


@router.post("/", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    service: SearchService = Depends(get_search_service),
):
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    try:
        history = [{"role": m.role, "content": m.content} for m in (request.chat_history or [])]
        result = await service.search(
            query=request.query,
            chat_history=history or None,
            topic=request.topic,
            doc_type=request.doc_type,
        )
        return SearchResponse(
            query=result["query"],
            refined_query=result["refined_query"],
            keywords=result["keywords"],
            results=result["results"],
            total_results=result["total_results"],
            timing=result["timing"],
        )
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
