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

        # Chunk → embed → upsert one page at a time, releasing each page's points before the
        # next. Only a single page's chunks + embeddings are ever in memory, not the whole
        # document's — which is what was blowing up RAM on large PDFs.
        chunks_by_level: dict[int, int] = {}
        level_2_preview: list[str] = []
        chunks_created = 0
        collection_ready = False

        # If any page fails (chunking, embedding, or upsert), roll the whole document back so
        # Qdrant is never left with a partially-uploaded file. All points are keyed by document_id.
        try:
            for group in self._chunker.iter_page_groups(
                document, document_id, topic=topic, doc_type=doc_type
            ):
                text_by_id = {meta.chunk_id: doc.text for doc, meta in group}
                content_embeddings = await self._embeddings.generate_embeddings_batch(
                    [doc.text for doc, _ in group]
                )

                if ingest_to_qdrant and not collection_ready:
                    await self._qdrant.initialize_collection(vector_size=len(content_embeddings[0]))
                    collection_ready = True

                qdrant_chunks: list[dict[str, Any]] = []
                qdrant_embeddings: list[dict[str, list[float]]] = []
                for (doc, meta), content_emb in zip(group, content_embeddings):
                    qdrant_chunks.append(
                        {
                            "chunk_id": meta.chunk_id,
                            "level": meta.level,
                            "document_id": meta.document_id,
                            "document_name": resolved_name,
                            "text": doc.text,
                            "file_type": "normal",
                            "parent_id": meta.parent_id,
                            "prev_chunk": text_by_id.get(meta.prev_chunk) if meta.prev_chunk else None,
                            "next_chunk": text_by_id.get(meta.next_chunk) if meta.next_chunk else None,
                            "page_number": meta.page_number,
                            "topic": topic,
                            "doc_type": doc_type,
                        }
                    )
                    qdrant_embeddings.append({"content": content_emb})
                    chunks_by_level[meta.level] = chunks_by_level.get(meta.level, 0) + 1
                    if meta.level == 2 and len(level_2_preview) < 5:
                        t = doc.text
                        level_2_preview.append(t[:300] + ("…" if len(t) > 300 else ""))

                if ingest_to_qdrant:
                    await self._qdrant.upsert_chunks(qdrant_chunks, qdrant_embeddings)
                chunks_created += len(group)
        except Exception:
            logger.exception(
                "[ingest] failed for %r after %d chunk(s); rolling back document_id=%s",
                filename,
                chunks_created,
                document_id,
            )
            if ingest_to_qdrant:
                try:
                    removed = await self._qdrant.delete_document(document_id)
                    logger.info("[ingest] rollback removed %d chunk(s) for %r", removed, filename)
                except Exception:
                    logger.exception(
                        "[ingest] ROLLBACK FAILED for document_id=%s — manual cleanup needed",
                        document_id,
                    )
            raise

        if chunks_created == 0:
            logger.warning("[ingest] no chunks for %r", filename)
        else:
            logger.info("[ingest] indexed %d chunks for %r", chunks_created, filename)

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
