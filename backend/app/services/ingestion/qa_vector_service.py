"""Upsert QA pairs into Qdrant with question + answer vectors."""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from qdrant_client.models import PayloadSchemaType, PointStruct, SparseVector

from backend.app.infrastructure.openai.embeddings import EmbeddingService
from backend.app.infrastructure.qdrant.client import QdrantClient
from backend.app.services.ingestion.qa_models import QaPairInput
from backend.app.services.ingestion.qa_pair_builder import qa_pair_to_qdrant_payload
from backend.app.services.ingestion.transcript.schemas import ProcessedTranscript

logger = logging.getLogger(__name__)


def processed_transcript_to_pairs(
    processed: ProcessedTranscript,
    *,
    ingest_batch_id: str,
) -> list[dict[str, Any]]:
    """Convert ProcessedTranscript QA groups into Qdrant-ready pair dicts (UUID per pair)."""
    pairs: list[dict[str, Any]] = []
    client = processed.client
    folder = processed.source_folder

    for qa in processed.qa_groups:
        question = qa.question.strip()
        answer = qa.answer.strip()
        if not question or not answer:
            continue
        base = qa_pair_to_qdrant_payload(
            QaPairInput(
                question=question,
                answer=answer,
                tags=qa.tags,
                reasoning=qa.reasoning,
                document_name=client,
                source="transcript",
            ),
            ingest_batch_id=ingest_batch_id,
        )
        base["source_folder"] = folder
        base["meeting_date"] = processed.meeting_date
        pairs.append(base)
    return pairs


class QaVectorService:
    def __init__(
        self,
        qdrant: QdrantClient | None = None,
        embeddings: EmbeddingService | None = None,
    ) -> None:
        self._qdrant = qdrant or QdrantClient()
        self._embeddings = embeddings or EmbeddingService()

    async def _ensure_tags_index(self) -> None:
        try:
            await asyncio.to_thread(
                self._qdrant.client.create_payload_index,
                collection_name=self._qdrant.collection_name,
                field_name="tags",
                field_schema=PayloadSchemaType.KEYWORD,
            )
        except Exception as e:
            if "already" not in str(e).lower():
                logger.warning("Could not create tags index: %s", e)

    async def upsert_qa_pairs(self, pairs: list[dict[str, Any]]) -> int:
        if not pairs:
            return 0

        await asyncio.to_thread(self._qdrant.client.get_collections)
        await self._ensure_tags_index()

        questions = [p["text"] for p in pairs]
        answers = [p["answer"] for p in pairs]

        logger.info("[ingest] embedding %d QA questions and answers", len(pairs))
        question_embeddings = await self._embeddings.generate_embeddings_batch(questions)
        answer_embeddings = await self._embeddings.generate_embeddings_batch(answers)

        # "Last modified" time for this batch. QA pairs from transcripts also carry a
        # meeting_date (when the advice was actually given), which retrieval prefers;
        # ingested_at is the fallback recency signal for spreadsheet/chat pairs.
        ingested_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

        points: list[PointStruct] = []
        for pair, q_emb, a_emb in zip(pairs, question_embeddings, answer_embeddings):
            vector: dict[str, Any] = {
                "content": q_emb,
                "answer_content": a_emb,
            }
            sv = await self._qdrant._generate_sparse_vector(pair["answer"])
            if sv:
                vector["answer_content_sparse"] = SparseVector(
                    indices=sv["indices"],
                    values=sv["values"],
                )

            payload = {k: v for k, v in pair.items() if k not in ("point_id", "chunk_id")}
            payload["chunk_id"] = pair["chunk_id"]
            payload["ingested_at"] = ingested_at

            points.append(
                PointStruct(
                    id=pair["point_id"],
                    vector=vector,
                    payload=payload,
                )
            )

        batch_size = 50
        total = 0
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            await asyncio.to_thread(
                self._qdrant.client.upsert,
                collection_name=self._qdrant.collection_name,
                points=batch,
            )
            total += len(batch)
            logger.info("[ingest] upserted %d/%d QA points", total, len(points))

        return total
