"""Document models for hierarchical KB ingestion."""
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Document:
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChunkMetadata:
    level: int
    document_id: str
    chunk_id: str
    parent_id: Optional[str] = None
    prev_chunk: Optional[str] = None
    next_chunk: Optional[str] = None
    page_number: Optional[int] = None
    topic: Optional[str] = None
    doc_type: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "parent_id": self.parent_id,
            "prev_chunk": self.prev_chunk,
            "next_chunk": self.next_chunk,
            "page_number": self.page_number,
            "topic": self.topic,
            "doc_type": self.doc_type,
        }
