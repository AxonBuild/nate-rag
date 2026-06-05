"""Stable identifiers for ingested QA pairs and KB documents."""
import hashlib
import re
import uuid
from pathlib import Path


def _normalize_qa_part(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def qa_content_key(question: str, answer: str) -> str:
    """Canonical key for a question+answer pair."""
    return f"{_normalize_qa_part(question)}\n{_normalize_qa_part(answer)}"


def qa_point_id(question: str, answer: str) -> str:
    """Stable Qdrant point id — same normalized Q+A upserts in place."""
    digest = hashlib.sha256(qa_content_key(question, answer).encode("utf-8")).hexdigest()
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"qa_pair_{digest}"))


def qa_chunk_id(question: str, answer: str) -> str:
    """Payload chunk_id aligned with point id for the same pair."""
    return qa_point_id(question, answer)


def qa_dedup_key(question: str) -> str:
    """Question-only hash for future lookup / replace-by-question."""
    normalized = _normalize_qa_part(question)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def new_ingest_batch_id() -> str:
    """Groups all pairs from one upload run."""
    return str(uuid.uuid4())


def _normalize_filename(filename: str) -> str:
    name = Path(filename).name.strip().lower()
    return re.sub(r"\s+", " ", name)


def normalize_document_text(text: str) -> str:
    """Canonical form of extracted text used for document identity."""
    text = text.strip().lower()
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def document_content_hash(text: str) -> str:
    return hashlib.sha256(normalize_document_text(text).encode("utf-8")).hexdigest()


def document_id_from_name_and_content(filename: str, text: str) -> str:
    """Stable document id — same filename + same ingested text upserts in place."""
    key = f"{_normalize_filename(filename)}\n{document_content_hash(text)}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"kb_doc_{digest}"))
