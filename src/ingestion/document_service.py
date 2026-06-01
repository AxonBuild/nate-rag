"""Document processing service — hierarchical ingestion with topic/doc_type metadata."""
import uuid
import logging
from typing import Optional

from src.ingestion.document_loader import load_document
from src.ingestion.chunking import HierarchicalChunker
from src.ingestion.embeddings import EmbeddingService
from src.ingestion.qdrant_client import QdrantClient
from src.ingestion.models import Document

logger = logging.getLogger(__name__)


class DocumentService:

    def __init__(self):
        self.chunker = HierarchicalChunker()
        self.embedding_service = EmbeddingService()
        self.qdrant_client = QdrantClient()

    async def process_and_index_document(
        self,
        file_bytes: bytes,
        filename: str,
        topic: Optional[str] = None,
        doc_type: Optional[str] = None,
    ) -> dict:
        """
        Load, chunk, embed and index a single document.

        Args:
            file_bytes: Raw file content (PDF or DOCX)
            filename: Original filename (used as document_name in Qdrant)
            topic: Advisory topic e.g. "STR Loophole", "Cost Segs"
            doc_type: Document type e.g. "guide", "outline", "seo", "pdf", "script", "research"

        Returns:
            Dict with document_id, chunks_created, chunks_by_level
        """
        document_id = str(uuid.uuid4())

        logger.info(f"Loading: {filename}  topic={topic}  doc_type={doc_type}")
        document = await load_document(file_bytes, filename)
        document_name = document.metadata.get("document_name") or filename

        # Chunk
        logger.info(f"Chunking: {filename}")
        chunked = self.chunker.chunk_document(document, document_id, topic=topic, doc_type=doc_type)

        if not chunked:
            logger.warning(f"No chunks produced for {filename} — skipping")
            return {"document_id": document_id, "chunks_created": 0, "chunks_by_level": {}}

        # Embed all chunks (content vectors)
        all_texts = [d.text for d, _ in chunked]
        logger.info(f"Embedding {len(all_texts)} chunks")
        content_embeddings = await self.embedding_service.generate_embeddings_batch(all_texts)

        # Build Qdrant payload list
        text_by_id = {m.chunk_id: d.text for d, m in chunked}
        qdrant_chunks = []
        qdrant_embeddings = []

        for (doc, meta), content_emb in zip(chunked, content_embeddings):
            prev_text = text_by_id.get(meta.prev_chunk) if meta.prev_chunk else None
            next_text = text_by_id.get(meta.next_chunk) if meta.next_chunk else None

            chunk_dict = {
                "chunk_id": meta.chunk_id,
                "level": meta.level,
                "document_id": meta.document_id,
                "document_name": document_name,
                "text": doc.text,
                "file_type": "normal",
                "parent_id": meta.parent_id,
                "prev_chunk": prev_text,
                "next_chunk": next_text,
                "page_number": meta.page_number,
                "topic": topic,
                "doc_type": doc_type,
            }

            qdrant_chunks.append(chunk_dict)
            qdrant_embeddings.append({"content": content_emb})

        # Initialize collection on first run
        await self.qdrant_client.initialize_collection(vector_size=len(content_embeddings[0]))

        logger.info(f"Upserting {len(qdrant_chunks)} chunks for {filename}")
        await self.qdrant_client.upsert_chunks(qdrant_chunks, qdrant_embeddings)

        chunks_by_level = {}
        for _, meta in chunked:
            chunks_by_level[meta.level] = chunks_by_level.get(meta.level, 0) + 1

        return {
            "document_id": document_id,
            "document_name": document_name,
            "chunks_created": len(chunked),
            "chunks_by_level": chunks_by_level,
            "topic": topic,
            "doc_type": doc_type,
        }
