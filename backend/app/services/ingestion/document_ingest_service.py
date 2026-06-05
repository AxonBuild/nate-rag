"""Ingest PDF/DOCX knowledge-base documents into Qdrant."""
import logging
from typing import Any

from backend.app.infrastructure.openai.embeddings import EmbeddingService
from backend.app.infrastructure.qdrant.client import QdrantClient
from backend.app.services.ingestion.document.chunking import HierarchicalChunker
from backend.app.services.ingestion.document.loader import load_document
from backend.app.services.ingestion.ids import document_id_from_name_and_content

logger = logging.getLogger(__name__)


class DocumentIngestService:
    def __init__(
        self,
        chunker: HierarchicalChunker | None = None,
        embeddings: EmbeddingService | None = None,
        qdrant: QdrantClient | None = None,
    ) -> None:
        self._chunker = chunker or HierarchicalChunker()
        self._embeddings = embeddings or EmbeddingService()
        self._qdrant = qdrant or QdrantClient()

    async def process_and_index(
        self,
        file_bytes: bytes,
        filename: str,
        *,
        document_name: str | None = None,
        topic: str | None = None,
        doc_type: str | None = None,
        ingest_to_qdrant: bool = True,
    ) -> dict[str, Any]:
        resolved_name = (document_name or "").strip() or filename

        document = await load_document(file_bytes, filename)
        document_id = document_id_from_name_and_content(filename, document.text)
        if document_name:
            document.metadata["document_name"] = resolved_name

        logger.info(
            "[ingest] document load filename=%r name=%r document_id=%s topic=%r doc_type=%r",
            filename,
            resolved_name,
            document_id,
            topic,
            doc_type,
        )

        chunked = self._chunker.chunk_document(
            document,
            document_id,
            topic=topic,
            doc_type=doc_type,
        )

        if not chunked:
            logger.warning("[ingest] no chunks for %r", filename)
            return {
                "document_id": document_id,
                "document_name": resolved_name,
                "character_count": len(document.text),
                "chunks_created": 0,
                "chunks_by_level": {},
                "topic": topic,
                "doc_type": doc_type,
            }

        all_texts = [doc.text for doc, _ in chunked]
        logger.info("[ingest] embedding %d chunks for %r", len(all_texts), filename)
        content_embeddings = await self._embeddings.generate_embeddings_batch(all_texts)

        text_by_id = {meta.chunk_id: doc.text for doc, meta in chunked}
        qdrant_chunks: list[dict[str, Any]] = []
        qdrant_embeddings: list[dict[str, list[float]]] = []

        for (doc, meta), content_emb in zip(chunked, content_embeddings):
            prev_text = text_by_id.get(meta.prev_chunk) if meta.prev_chunk else None
            next_text = text_by_id.get(meta.next_chunk) if meta.next_chunk else None

            qdrant_chunks.append(
                {
                    "chunk_id": meta.chunk_id,
                    "level": meta.level,
                    "document_id": meta.document_id,
                    "document_name": resolved_name,
                    "text": doc.text,
                    "file_type": "normal",
                    "parent_id": meta.parent_id,
                    "prev_chunk": prev_text,
                    "next_chunk": next_text,
                    "page_number": meta.page_number,
                    "topic": topic,
                    "doc_type": doc_type,
                }
            )
            qdrant_embeddings.append({"content": content_emb})

        chunks_created = len(chunked)
        if ingest_to_qdrant:
            await self._qdrant.initialize_collection(
                vector_size=len(content_embeddings[0]),
            )
            await self._qdrant.upsert_chunks(qdrant_chunks, qdrant_embeddings)

        chunks_by_level: dict[int, int] = {}
        for _, meta in chunked:
            chunks_by_level[meta.level] = chunks_by_level.get(meta.level, 0) + 1

        level_2_preview = [
            c["text"][:300] + ("…" if len(c["text"]) > 300 else "")
            for c in qdrant_chunks
            if c["level"] == 2
        ][:5]

        return {
            "document_id": document_id,
            "document_name": resolved_name,
            "character_count": len(document.text),
            "chunks_created": chunks_created,
            "chunks_by_level": chunks_by_level,
            "topic": topic,
            "doc_type": doc_type,
            "preview": level_2_preview,
        }
