"""Qdrant client — same as tom-orent-RAG with topic/doc_type indexes added."""
import uuid
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from qdrant_client import QdrantClient as QdrantSyncClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition,
    MatchValue, MatchAny, Prefetch, Fusion, FusionQuery,
    PayloadSchemaType, TextIndexParams, SparseVector, SparseVectorParams, Modifier,
)
from fastembed import SparseTextEmbedding
from backend.app.config.settings import settings

logger = logging.getLogger(__name__)


class QdrantClient:

    def __init__(self):
        if settings.qdrant_url:
            self.client = QdrantSyncClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
                timeout=settings.qdrant_timeout,
            )
        else:
            self.client = QdrantSyncClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                https=settings.qdrant_https,
                api_key=settings.qdrant_api_key,
                timeout=settings.qdrant_timeout,
            )
        self.collection_name = settings.qdrant_collection_name
        self._sparse_model = None

    @staticmethod
    def _to_point_id(chunk_id: str) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))

    async def _ensure_payload_indexes(self) -> None:
        async def _create(field: str, schema: PayloadSchemaType) -> None:
            try:
                await asyncio.to_thread(
                    self.client.create_payload_index,
                    collection_name=self.collection_name,
                    field_name=field,
                    field_schema=schema,
                )
                logger.info(f"Created payload index: {field}")
            except Exception as e:
                if "already" in str(e).lower() and "exist" in str(e).lower():
                    return
                logger.warning(f"Could not create payload index for '{field}': {e}")

        for field in ("document_id", "document_name", "chunk_id", "parent_id", "file_type", "topic", "doc_type"):
            await _create(field, PayloadSchemaType.KEYWORD)
        for field in ("level", "page_number"):
            await _create(field, PayloadSchemaType.INTEGER)

        # Full-text index on chunk text
        try:
            await asyncio.to_thread(
                self.client.create_payload_index,
                collection_name=self.collection_name,
                field_name="text",
                field_schema=TextIndexParams(
                    type="text", tokenizer="word", min_token_len=2, max_token_len=20, lowercase=True
                ),
            )
        except Exception as e:
            if "already" not in str(e).lower():
                logger.warning(f"Could not create text index: {e}")

    async def initialize_collection(self, vector_size: Optional[int] = None) -> None:
        if vector_size is None:
            vector_size = settings.embedding_dimension

        collections = await asyncio.to_thread(self.client.get_collections)
        existing = [c.name for c in collections.collections]

        if self.collection_name not in existing:
            await asyncio.to_thread(
                self.client.create_collection,
                collection_name=self.collection_name,
                vectors_config={
                    "content": VectorParams(size=vector_size, distance=Distance.COSINE),
                },
                sparse_vectors_config={
                    "content_sparse": SparseVectorParams(modifier=Modifier.IDF)
                },
            )
            logger.info(f"Created collection: {self.collection_name} (dim={vector_size})")
        else:
            logger.info(f"Collection already exists: {self.collection_name}")

        await self._ensure_payload_indexes()

    async def _get_sparse_model(self) -> SparseTextEmbedding:
        if self._sparse_model is None:
            self._sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
        return self._sparse_model

    async def _generate_sparse_vector(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            model = await self._get_sparse_model()
            embeddings = list(model.embed([text]))
            if embeddings:
                e = embeddings[0]
                return {"indices": e.indices.tolist(), "values": e.values.tolist()}
        except Exception as ex:
            logger.warning(f"Sparse vector generation failed: {ex}")
        return None

    async def upsert_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[Any],
    ) -> None:
        model = await self._get_sparse_model()
        points = []

        # When this batch is written — used downstream as the chunk's "last modified"
        # time so the LLM can prefer the most recent source when context conflicts.
        ingested_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

        for chunk, embedding in zip(chunks, embeddings):
            level = chunk["level"]
            text = chunk.get("text", "")

            # Build dense vector
            content_emb = embedding.get("content") if isinstance(embedding, dict) else embedding
            vector = {"content": content_emb}

            # Sparse vector for Level 2
            if level == 2 and text:
                try:
                    sparse_embs = list(model.embed([text]))
                    if sparse_embs:
                        se = sparse_embs[0]
                        vector["content_sparse"] = SparseVector(
                            indices=se.indices.tolist(), values=se.values.tolist()
                        )
                except Exception as ex:
                    logger.warning(f"Sparse vector failed for chunk {chunk['chunk_id']}: {ex}")

            payload = {
                "level": level,
                "document_id": chunk["document_id"],
                "document_name": chunk.get("document_name"),
                "chunk_id": chunk["chunk_id"],
                "text": text,
                "file_type": chunk.get("file_type", "normal"),
                "parent_id": chunk.get("parent_id"),
                "prev_chunk": chunk.get("prev_chunk"),
                "next_chunk": chunk.get("next_chunk"),
                "page_number": chunk.get("page_number"),
                # Nate KB fields
                "topic": chunk.get("topic"),
                "doc_type": chunk.get("doc_type"),
                "ingested_at": ingested_at,
            }

            points.append(PointStruct(
                id=self._to_point_id(chunk["chunk_id"]),
                vector=vector,
                payload=payload,
            ))

        batch_size = 50
        for i in range(0, len(points), batch_size):
            await asyncio.to_thread(
                self.client.upsert,
                collection_name=self.collection_name,
                points=points[i:i + batch_size],
            )
        logger.info(f"Upserted {len(points)} chunks to '{self.collection_name}'")
