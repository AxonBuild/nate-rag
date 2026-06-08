from fastapi import APIRouter

from backend.app.config.settings import settings

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health")
async def health():
    return {"status": "healthy"}


@router.get("/config")
async def config():
    return {
        "qdrant_collection_name": settings.qdrant_collection_name,
        "openai_embedding_model": settings.openai_embedding_model,
        "openai_model": settings.openai_model,
    }
