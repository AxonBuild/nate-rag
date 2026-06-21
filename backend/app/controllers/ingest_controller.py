from backend.app.schemas.ingest import (
    DeleteDocumentResponse,
    DocumentIngestResponse,
    DocumentListItem,
    ProcessedTranscriptResponse,
    QaColumnsPreviewResponse,
    QaIngestResponse,
    QaPreviewRow,
    TranscriptIngestResponse,
    TranscriptIngestUsage,
    TranscriptQAGroupResponse,
)
from backend.app.services.ingestion.qa_sheet_parser import spreadsheet_columns
from backend.app.services.ingestion.document_ingest_service import DocumentIngestService
from backend.app.services.ingestion.qa_ingest_service import QaIngestService
from backend.app.services.ingestion.transcript.schemas import ProcessedTranscript
from backend.app.services.ingestion.transcript_ingest_service import TranscriptIngestService


class IngestController:
    def __init__(
        self,
        transcript_service: TranscriptIngestService,
        qa_service: QaIngestService | None = None,
        document_service: DocumentIngestService | None = None,
    ):
        self._transcript = transcript_service
        self._qa = qa_service or QaIngestService()
        self._document = document_service or DocumentIngestService()

    @staticmethod
    def _to_response(processed: ProcessedTranscript) -> ProcessedTranscriptResponse:
        return ProcessedTranscriptResponse(
            client=processed.client,
            meeting_title=processed.meeting_title,
            meeting_date=processed.meeting_date,
            duration_minutes=processed.duration_minutes,
            source_folder=processed.source_folder,
            attendees=processed.attendees,
            speakers=processed.speakers,
            total_utterances=processed.total_utterances,
            skipped_utterances=processed.skipped_utterances,
            qa_groups=[
                TranscriptQAGroupResponse(
                    question=g.question,
                    tags=g.tags,
                    reasoning=g.reasoning,
                    answer=g.answer,
                    confidence=g.confidence,
                    advisor_utterance_indices=g.advisor_utterance_indices,
                )
                for g in processed.qa_groups
            ],
        )

    async def ingest_transcript(
        self,
        transcript_bytes: bytes,
        *,
        metadata_bytes: bytes | None = None,
        client_name: str | None = None,
        ingest_to_qdrant: bool = True,
        model: str | None = None,
    ) -> TranscriptIngestResponse:
        result = await self._transcript.process_from_upload(
            transcript_bytes,
            metadata_bytes=metadata_bytes,
            client_name=client_name,
            ingest_to_qdrant=ingest_to_qdrant,
            model=model,
        )
        processed: ProcessedTranscript = result["processed"]
        usage = result["usage"]

        return TranscriptIngestResponse(
            processed=self._to_response(processed),
            cost_usd=round(result["cost_usd"], 6),
            usage=TranscriptIngestUsage(
                input_tokens=usage["input_tokens"],
                output_tokens=usage["output_tokens"],
                chunks=usage["chunks"],
            ),
            ingested_points=result["ingested_points"],
            model=result["model"],
        )

    @staticmethod
    def preview_qa_columns(file_bytes: bytes, filename: str) -> QaColumnsPreviewResponse:
        return QaColumnsPreviewResponse(columns=spreadsheet_columns(file_bytes, filename))

    async def ingest_qa_spreadsheet(
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
    ) -> QaIngestResponse:
        result = await self._qa.ingest_spreadsheet(
            file_bytes,
            filename,
            question_column=question_column,
            answer_column=answer_column,
            tags_column=tags_column,
            document_name_column=document_name_column,
            default_document_name=default_document_name,
            ingest_to_qdrant=ingest_to_qdrant,
        )
        stats = result["stats"]
        return QaIngestResponse(
            ingest_batch_id=stats.ingest_batch_id,
            columns=result["columns"],
            total_rows=stats.total_rows,
            valid_rows=stats.valid_rows,
            skipped_empty=stats.skipped_empty,
            ingested_points=stats.ingested_points,
            preview=[
                QaPreviewRow(
                    question=p["question"],
                    answer=p["answer"],
                    document_name=p["document_name"],
                    tags=p["tags"],
                )
                for p in result["preview"]
            ],
        )

    async def ingest_document(
        self,
        file_bytes: bytes,
        filename: str,
        *,
        document_name: str | None = None,
        topic: str | None = None,
        doc_type: str | None = None,
        ingest_to_qdrant: bool = True,
    ) -> DocumentIngestResponse:
        result = await self._document.process_and_index(
            file_bytes,
            filename,
            document_name=document_name,
            topic=topic,
            doc_type=doc_type,
            ingest_to_qdrant=ingest_to_qdrant,
        )
        return DocumentIngestResponse(
            document_id=result["document_id"],
            document_name=result["document_name"],
            character_count=result["character_count"],
            chunks_created=result["chunks_created"],
            chunks_by_level=result["chunks_by_level"],
            topic=result.get("topic"),
            doc_type=result.get("doc_type"),
            preview=result.get("preview", []),
        )

    async def list_documents(self) -> list[DocumentListItem]:
        docs = await self._document.list_documents()
        return [DocumentListItem(**d) for d in docs]

    async def delete_document(self, document_id: str) -> DeleteDocumentResponse:
        deleted = await self._document.delete_document(document_id)
        return DeleteDocumentResponse(document_id=document_id, deleted_chunks=deleted)
