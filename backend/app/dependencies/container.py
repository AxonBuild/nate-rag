"""FastAPI dependency injection."""
from functools import lru_cache

from backend.app.infrastructure.qdrant.client import QdrantClient
from backend.app.services.admin_service import AdminService
from backend.app.services.chat_service import ChatService
from backend.app.services.conversation_service import ConversationService
from backend.app.services.rag.search_service import SearchService
from backend.app.services.ingestion.document_ingest_service import DocumentIngestService
from backend.app.services.ingestion.qa_ingest_service import QaIngestService
from backend.app.services.ingestion.transcript_ingest_service import TranscriptIngestService
from backend.app.services.user_settings_service import UserSettingsService


@lru_cache
def get_search_service() -> SearchService:
    return SearchService()


@lru_cache
def get_qdrant_client() -> QdrantClient:
    return QdrantClient()


@lru_cache
def get_chat_service() -> ChatService:
    return ChatService(get_search_service())


@lru_cache
def get_conversation_service() -> ConversationService:
    return ConversationService()


@lru_cache
def get_admin_service() -> AdminService:
    return AdminService()


@lru_cache
def get_user_settings_service() -> UserSettingsService:
    return UserSettingsService()


@lru_cache
def get_transcript_ingest_service() -> TranscriptIngestService:
    return TranscriptIngestService()


@lru_cache
def get_qa_ingest_service() -> QaIngestService:
    return QaIngestService()


@lru_cache
def get_document_ingest_service() -> DocumentIngestService:
    return DocumentIngestService()
