"""Build Qdrant-ready QA pair dicts with content-hash identities."""
from typing import Any

from backend.app.services.ingestion.ids import qa_chunk_id, qa_dedup_key, qa_point_id
from backend.app.services.ingestion.qa_models import QaPairInput


def qa_pair_to_qdrant_payload(
    pair: QaPairInput,
    *,
    ingest_batch_id: str,
) -> dict[str, Any]:
    """Stable id from normalized question+answer — re-upload upserts, no duplicates."""
    question = pair.question.strip()
    answer = pair.answer.strip()
    point_id = qa_point_id(question, answer)
    return {
        "chunk_id": qa_chunk_id(question, answer),
        "point_id": point_id,
        "text": question,
        "answer": answer,
        "tags": pair.tags or [],
        "reasoning": pair.reasoning or "",
        "document_name": pair.document_name or "Unknown",
        "source": pair.source,
        "ingest_batch_id": ingest_batch_id,
        "dedup_key": qa_dedup_key(question),
        "doc_type": "qa_pair",
        "file_type": "qa_pair",
        "topic": None,
        "level": None,
        "parent_id": None,
        "prev_chunk": None,
        "next_chunk": None,
        "page_number": None,
    }


def rows_to_qa_pairs(
    rows: list[QaPairInput],
    *,
    ingest_batch_id: str,
) -> list[dict[str, Any]]:
    return [qa_pair_to_qdrant_payload(r, ingest_batch_id=ingest_batch_id) for r in rows]
