import logging

from fastapi import APIRouter, Depends, HTTPException

from backend.app.controllers.search_controller import SearchController
from backend.app.dependencies.container import get_search_service
from backend.app.schemas.search import SearchRequestSchema, SearchResponseSchema
from backend.app.services.rag.search_service import SearchService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search"])


def get_search_controller(
    search_service: SearchService = Depends(get_search_service),
) -> SearchController:
    return SearchController(search_service)


@router.post("/", response_model=SearchResponseSchema)
async def search(
    request: SearchRequestSchema,
    controller: SearchController = Depends(get_search_controller),
):
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    try:
        return await controller.search(request)
    except Exception as e:
        logger.error("Search error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e
