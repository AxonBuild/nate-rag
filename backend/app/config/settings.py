"""Ingestion pipeline settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field
from typing import Optional

EMBEDDING_DIMENSIONS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
}


class Settings(BaseSettings):
    # OpenAI / OpenRouter
    openai_api_key: str
    openai_base_url: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openai_refinement_model: Optional[str] = None
    openai_verification_model: Optional[str] = None
    openai_transcript_model: Optional[str] = None
    openai_embedding_model: str = "text-embedding-3-large"
    enable_answer_verification: bool = True

    # Chat persistence
    database_url: str = "sqlite+aiosqlite:///./data/nate.db"

    @computed_field
    @property
    def embedding_dimension(self) -> int:
        return EMBEDDING_DIMENSIONS.get(self.openai_embedding_model, 3072)

    # Qdrant
    qdrant_url: Optional[str] = None
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_https: bool = False
    qdrant_collection_name: str = "nate-rag-docs"
    qdrant_api_key: Optional[str] = None
    qdrant_timeout: int = 120

    # Chunking
    chunk_size_page: int = 1200
    chunk_size_paragraph: int = 400
    chunk_size_content: int = 150
    chunk_overlap: int = 0

    # Retrieval
    retrieval_limit_pages: int = 5
    retrieval_limit_paragraphs: int = 10
    retrieval_limit_final: int = 5
    retrieval_page_prefetch_limit: int = 20
    retrieval_content_prefetch_limit: int = 20
    retrieval_min_score_final: float = 0.4
    use_keyword_search_level2: bool = True

    # Clerk (auth + admin invites)
    clerk_secret_key: Optional[str] = None
    clerk_publishable_key: Optional[str] = None
    clerk_issuer: Optional[str] = None
    clerk_invite_redirect_url: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
