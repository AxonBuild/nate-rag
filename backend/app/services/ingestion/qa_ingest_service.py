"""Ingest QA pairs from spreadsheets (CSV / XLSX) into Qdrant."""
import logging

from backend.app.services.ingestion.ids import new_ingest_batch_id
from backend.app.services.ingestion.qa_models import QaIngestStats, QaPairInput
from backend.app.services.ingestion.qa_pair_builder import rows_to_qa_pairs
from backend.app.services.ingestion.qa_sheet_parser import parse_spreadsheet_bytes
from backend.app.services.ingestion.qa_vector_service import QaVectorService

logger = logging.getLogger(__name__)


class QaIngestService:
    def __init__(self, qa_vectors: QaVectorService | None = None) -> None:
        self._qa_vectors = qa_vectors or QaVectorService()

    async def ingest_spreadsheet(
        self,
        file_bytes: bytes,
        filename: str,
        *,
        question_column: str,
        answer_column: str,
        tags_column: str | None = None,
        document_name_column: str | None = None,
        default_document_name: str = "Unknown",
        ingest_to_qdrant: bool = True,
    ) -> dict:
        pairs, total_rows, skipped_empty, columns = parse_spreadsheet_bytes(
            file_bytes,
            filename,
            question_column=question_column,
            answer_column=answer_column,
            tags_column=tags_column,
            document_name_column=document_name_column,
            default_document_name=default_document_name,
        )

        ingest_batch_id = new_ingest_batch_id()
        ingested_points = 0

        if ingest_to_qdrant and pairs:
            qdrant_pairs = rows_to_qa_pairs(pairs, ingest_batch_id=ingest_batch_id)
            ingested_points = await self._qa_vectors.upsert_qa_pairs(qdrant_pairs)

        stats = QaIngestStats(
            ingest_batch_id=ingest_batch_id,
            total_rows=total_rows,
            valid_rows=len(pairs),
            skipped_empty=skipped_empty,
            ingested_points=ingested_points,
        )

        logger.info(
            "[ingest] qa spreadsheet batch=%s valid=%d skipped=%d ingested=%d",
            ingest_batch_id,
            stats.valid_rows,
            stats.skipped_empty,
            stats.ingested_points,
        )

        return {
            "stats": stats,
            "columns": columns,
            "preview": [
                {
                    "question": p.question,
                    "answer": p.answer[:200] + ("…" if len(p.answer) > 200 else ""),
                    "document_name": p.document_name,
                    "tags": p.tags,
                }
                for p in pairs[:20]
            ],
        }

    async def ingest_pairs(
        self,
        pairs: list[QaPairInput],
        *,
        ingest_to_qdrant: bool = True,
    ) -> QaIngestStats:
        ingest_batch_id = new_ingest_batch_id()
        ingested_points = 0
        if ingest_to_qdrant and pairs:
            qdrant_pairs = rows_to_qa_pairs(pairs, ingest_batch_id=ingest_batch_id)
            ingested_points = await self._qa_vectors.upsert_qa_pairs(qdrant_pairs)

        return QaIngestStats(
            ingest_batch_id=ingest_batch_id,
            total_rows=len(pairs),
            valid_rows=len(pairs),
            skipped_empty=0,
            ingested_points=ingested_points,
        )
