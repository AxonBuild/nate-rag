from typing import Any, Literal

from pydantic import BaseModel, Field


class TranscriptQAGroupResponse(BaseModel):
    question: str
    tags: list[str]
    reasoning: str
    answer: str
    confidence: Literal["high", "medium", "low"]
    advisor_utterance_indices: list[int]


class ProcessedTranscriptResponse(BaseModel):
    client: str
    meeting_title: str
    meeting_date: str
    duration_minutes: int
    source_folder: str
    attendees: list[str]
    speakers: list[str]
    total_utterances: int
    skipped_utterances: int
    qa_groups: list[TranscriptQAGroupResponse]


class TranscriptIngestUsage(BaseModel):
    input_tokens: int
    output_tokens: int
    chunks: int


class TranscriptIngestResponse(BaseModel):
    processed: ProcessedTranscriptResponse
    cost_usd: float
    usage: TranscriptIngestUsage
    ingested_points: int
    model: str = Field(description="LLM model used for QA extraction")


class QaPreviewRow(BaseModel):
    question: str
    answer: str
    document_name: str
    tags: list[str] = Field(default_factory=list)


class DocumentIngestResponse(BaseModel):
    document_id: str
    document_name: str
    character_count: int
    chunks_created: int
    chunks_by_level: dict[int, int] = Field(default_factory=dict)
    topic: str | None = None
    doc_type: str | None = None
    preview: list[str] = Field(
        default_factory=list,
        description="First few level-2 chunk snippets (searchable content)",
    )


class QaColumnsPreviewResponse(BaseModel):
    columns: list[str]


class QaIngestResponse(BaseModel):
    ingest_batch_id: str = Field(
        description="UUID grouping all pairs from this upload; use for audit or future delete-by-batch"
    )
    columns: list[str]
    total_rows: int
    valid_rows: int
    skipped_empty: int
    ingested_points: int
    preview: list[QaPreviewRow] = Field(default_factory=list)
