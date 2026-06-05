"""Shared QA pair shapes for spreadsheet and API ingest."""
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class QaPairInput(BaseModel):
    question: str
    answer: str
    tags: list[str] = Field(default_factory=list)
    reasoning: str = ""
    document_name: str = "Unknown"
    source: Literal["spreadsheet", "chat", "transcript"] = "spreadsheet"


class QaIngestStats(BaseModel):
    ingest_batch_id: str
    total_rows: int
    valid_rows: int
    skipped_empty: int
    ingested_points: int
