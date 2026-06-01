"""Shared FastAPI dependencies."""
from src.retrieval.search_service import SearchService
from src.ingestion.qdrant_client import QdrantClient


def get_search_service() -> SearchService:
    return SearchService()


def get_qdrant_client() -> QdrantClient:
    return QdrantClient()
