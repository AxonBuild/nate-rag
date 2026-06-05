"""Hierarchical chunking — page → paragraph → content levels."""
import re
from typing import List

from backend.app.config.settings import settings
from backend.app.services.ingestion.document.models import ChunkMetadata, Document


class HierarchicalChunker:
    @staticmethod
    def _split_by_words_at_sentence_boundary(text: str, chunk_size_words: int) -> List[str]:
        sentence_pattern = r"([^.!?]*[.!?]+)\s*"
        sentences = re.findall(sentence_pattern, text)

        remaining = re.sub(sentence_pattern, "", text).strip()
        if remaining:
            sentences.append(remaining)

        chunks: list[str] = []
        current: list[str] = []
        word_count = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            current.append(sentence)
            word_count += len(sentence.split())
            if word_count >= chunk_size_words:
                chunks.append(" ".join(current))
                current, word_count = [], 0

        if current:
            chunks.append(" ".join(current))

        return chunks

    def chunk_document(
        self,
        document: Document,
        document_id: str,
        topic: str | None = None,
        doc_type: str | None = None,
    ) -> list[tuple[Document, ChunkMetadata]]:
        page_chunks = self._create_page_chunks(document, document_id, topic, doc_type)
        paragraph_chunks = self._create_paragraph_chunks(page_chunks, document_id, topic, doc_type)
        content_chunks = self._create_content_chunks(paragraph_chunks, document_id, topic, doc_type)
        return page_chunks + paragraph_chunks + content_chunks

    def _create_page_chunks(
        self, document: Document, document_id: str, topic: str | None, doc_type: str | None
    ) -> list[tuple[Document, ChunkMetadata]]:
        texts = self._split_by_words_at_sentence_boundary(
            document.text, settings.chunk_size_page
        )
        chunks: list[tuple[Document, ChunkMetadata]] = []
        for i, text in enumerate(texts):
            chunk_id = f"{document_id}_page_{i}"
            meta = ChunkMetadata(
                level=0,
                document_id=document_id,
                chunk_id=chunk_id,
                page_number=i,
                topic=topic,
                doc_type=doc_type,
            )
            chunks.append(
                (Document(text=text, metadata={**document.metadata, **meta.to_dict()}), meta)
            )
        return chunks

    def _create_paragraph_chunks(
        self,
        page_chunks: list[tuple[Document, ChunkMetadata]],
        document_id: str,
        topic: str | None,
        doc_type: str | None,
    ) -> list[tuple[Document, ChunkMetadata]]:
        chunks: list[tuple[Document, ChunkMetadata]] = []
        for page_doc, page_meta in page_chunks:
            texts = self._split_by_words_at_sentence_boundary(
                page_doc.text, settings.chunk_size_paragraph
            )
            for i, text in enumerate(texts):
                chunk_id = f"{document_id}_paragraph_{page_meta.chunk_id}_{i}"
                meta = ChunkMetadata(
                    level=1,
                    document_id=document_id,
                    chunk_id=chunk_id,
                    parent_id=page_meta.chunk_id,
                    page_number=page_meta.page_number,
                    topic=topic,
                    doc_type=doc_type,
                )
                chunks.append(
                    (Document(text=text, metadata={**page_doc.metadata, **meta.to_dict()}), meta)
                )
        return chunks

    def _create_content_chunks(
        self,
        paragraph_chunks: list[tuple[Document, ChunkMetadata]],
        document_id: str,
        topic: str | None,
        doc_type: str | None,
    ) -> list[tuple[Document, ChunkMetadata]]:
        chunks: list[tuple[Document, ChunkMetadata]] = []
        for para_doc, para_meta in paragraph_chunks:
            texts = self._split_by_words_at_sentence_boundary(
                para_doc.text, settings.chunk_size_content
            )
            for i, text in enumerate(texts):
                chunk_id = f"{document_id}_content_{para_meta.chunk_id}_{i}"
                meta = ChunkMetadata(
                    level=2,
                    document_id=document_id,
                    chunk_id=chunk_id,
                    parent_id=para_meta.chunk_id,
                    page_number=para_meta.page_number,
                    topic=topic,
                    doc_type=doc_type,
                )
                chunks.append(
                    (Document(text=text, metadata={**para_doc.metadata, **meta.to_dict()}), meta)
                )

        self._link_content_chunks(chunks)
        return chunks

    def _link_content_chunks(self, chunks: list[tuple[Document, ChunkMetadata]]) -> None:
        by_parent: dict[str, list[tuple[Document, ChunkMetadata]]] = {}
        for doc, meta in chunks:
            if meta.parent_id:
                by_parent.setdefault(meta.parent_id, []).append((doc, meta))

        for siblings in by_parent.values():
            siblings.sort(key=lambda x: x[1].chunk_id)
            for i, (doc, meta) in enumerate(siblings):
                if i > 0:
                    meta.prev_chunk = siblings[i - 1][1].chunk_id
                if i < len(siblings) - 1:
                    meta.next_chunk = siblings[i + 1][1].chunk_id
                doc.metadata.update(meta.to_dict())
