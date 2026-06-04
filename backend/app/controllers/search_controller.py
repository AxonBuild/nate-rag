import logging

from backend.app.schemas.search import SearchRequestSchema, SearchResponseSchema
from backend.app.services.rag.search_service import SearchService

logger = logging.getLogger(__name__)


class SearchController:
    def __init__(self, search_service: SearchService):
        self._search = search_service

    async def search(self, request: SearchRequestSchema) -> SearchResponseSchema:
        history = None
        if request.chat_history:
            history = [{"role": m.role, "content": m.content} for m in request.chat_history]
        result = await self._search.search(
            query=request.query,
            chat_history=history,
            topic=request.topic,
            doc_type=request.doc_type,
            retrieval_limit=request.retrieval_limit,
        )
        return SearchResponseSchema(
            query=result["query"],
            refined_query=result["refined_query"],
            keywords=result["keywords"],
            results=result["results"],
            total_results=result["total_results"],
            timing=result["timing"],
        )
