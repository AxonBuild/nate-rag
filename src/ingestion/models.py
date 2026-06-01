"""Document models for ingestion pipeline."""
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class Document:
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def page_content(self) -> str:
        return self.text


@dataclass
class ChunkMetadata:
    level: int
    document_id: str
    chunk_id: str
    parent_id: Optional[str] = None
    prev_chunk: Optional[str] = None
    next_chunk: Optional[str] = None
    page_number: Optional[int] = None
    summary: Optional[str] = None
    # Nate KB additions
    topic: Optional[str] = None
    doc_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "parent_id": self.parent_id,
            "prev_chunk": self.prev_chunk,
            "next_chunk": self.next_chunk,
            "page_number": self.page_number,
            "summary": self.summary,
            "topic": self.topic,
            "doc_type": self.doc_type,
        }


@dataclass
class DocumentChunk:
    text: str
    metadata: ChunkMetadata
    embedding: Optional[list[float]] = None
