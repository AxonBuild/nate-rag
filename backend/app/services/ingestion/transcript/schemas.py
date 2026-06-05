from typing import Literal

from pydantic import BaseModel, Field


class TranscriptQAGroup(BaseModel):
    question: str
    advisor_utterance_indices: list[int]
    client_utterance_indices: list[int]
    tags: list[str] = Field(min_length=2, max_length=5)
    reasoning: str
    answer: str
    confidence: Literal["high", "medium", "low"]


class TranscriptExtractionResult(BaseModel):
    qa_groups: list[TranscriptQAGroup]
    skipped_indices: list[int] = []


class TranscriptQAGroupFull(BaseModel):
    """Flattened QA group stored after reconstruction."""

    question: str
    tags: list[str]
    reasoning: str
    answer: str
    confidence: Literal["high", "medium", "low"]
    advisor_utterance_indices: list[int]


class ProcessedTranscript(BaseModel):
    """Output of transcript QA extraction for one meeting."""

    client: str
    meeting_title: str
    meeting_date: str
    duration_minutes: int
    source_folder: str
    attendees: list[str]
    speakers: list[str]
    total_utterances: int
    skipped_utterances: int
    qa_groups: list[TranscriptQAGroupFull]
