"""Orchestrates transcript upload → QA extraction → optional Qdrant ingest."""
import json
import logging
from typing import Any

from backend.app.services.ingestion.ids import new_ingest_batch_id
from backend.app.services.ingestion.qa_vector_service import (
    QaVectorService,
    processed_transcript_to_pairs,
)
from backend.app.services.ingestion.transcript.processor import TranscriptProcessor
from backend.app.services.ingestion.transcript.schemas import ProcessedTranscript

logger = logging.getLogger(__name__)


class TranscriptIngestService:
    def __init__(
        self,
        processor: TranscriptProcessor | None = None,
        qa_vectors: QaVectorService | None = None,
    ) -> None:
        self._processor = processor or TranscriptProcessor()
        self._qa_vectors = qa_vectors or QaVectorService()

    @staticmethod
    def parse_transcript_json(raw: bytes) -> dict[str, Any]:
        try:
            data = json.loads(raw.decode("utf-8"))
        except UnicodeDecodeError as e:
            raise ValueError("Transcript file must be UTF-8 encoded JSON") from e
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}") from e

        if not isinstance(data, dict):
            raise ValueError("Transcript JSON must be an object with a `data` array")
        if "data" not in data or not isinstance(data.get("data"), list):
            raise ValueError("Transcript JSON must contain a `data` array of utterances")
        return data

    @staticmethod
    def parse_metadata_json(raw: bytes | None) -> dict[str, Any]:
        if not raw:
            return {}
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            raise ValueError(f"Invalid metadata JSON: {e}") from e
        if not isinstance(data, dict):
            raise ValueError("Metadata JSON must be an object")
        return data

    async def process_and_ingest(
        self,
        transcript_json: dict[str, Any],
        *,
        client_name: str = "Unknown client",
        meeting_title: str | None = None,
        meeting_date: str | None = None,
        duration_minutes: int | None = None,
        source_folder: str | None = None,
        attendees: list[str] | None = None,
        ingest_to_qdrant: bool = True,
        model: str | None = None,
    ) -> dict[str, Any]:
        metadata_title = meeting_title
        metadata_date = meeting_date
        metadata_duration = duration_minutes
        metadata_attendees = attendees

        processed, cost_usd, usage = await self._processor.process_transcript_json(
            transcript_json,
            client_name=client_name,
            meeting_title=metadata_title,
            meeting_date=metadata_date,
            duration_minutes=metadata_duration,
            source_folder=source_folder,
            attendees=metadata_attendees,
            model=model,
        )

        ingested_points = 0
        ingest_batch_id = new_ingest_batch_id()
        if ingest_to_qdrant and processed.qa_groups:
            pairs = processed_transcript_to_pairs(
                processed,
                ingest_batch_id=ingest_batch_id,
            )
            ingested_points = await self._qa_vectors.upsert_qa_pairs(pairs)

        return {
            "processed": processed,
            "cost_usd": cost_usd,
            "usage": usage,
            "ingested_points": ingested_points,
            "model": model or self._processor._llm.model,
        }

    async def process_from_upload(
        self,
        transcript_bytes: bytes,
        *,
        metadata_bytes: bytes | None = None,
        client_name: str | None = None,
        ingest_to_qdrant: bool = True,
        model: str | None = None,
    ) -> dict[str, Any]:
        transcript_json = self.parse_transcript_json(transcript_bytes)
        metadata = self.parse_metadata_json(metadata_bytes)

        resolved_client = (
            client_name
            or metadata.get("client")
            or "Unknown client"
        )
        meeting_title = metadata.get("meetingTitle") or metadata.get("meeting_title")
        meeting_date_raw = metadata.get("meetingStartTime") or metadata.get("meeting_date") or ""
        meeting_date = str(meeting_date_raw)[:10] if meeting_date_raw else None
        duration = metadata.get("meetingDuration") or metadata.get("duration_minutes")
        duration_minutes = int(duration) if duration is not None else None
        source_folder = metadata.get("source_folder") or metadata.get("sourceFolder")
        attendees = metadata.get("attendees")
        if attendees is not None and not isinstance(attendees, list):
            attendees = None

        return await self.process_and_ingest(
            transcript_json,
            client_name=resolved_client,
            meeting_title=meeting_title,
            meeting_date=meeting_date,
            duration_minutes=duration_minutes,
            source_folder=source_folder,
            attendees=attendees,
            ingest_to_qdrant=ingest_to_qdrant,
            model=model,
        )
