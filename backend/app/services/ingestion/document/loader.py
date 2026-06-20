"""Load PDF and DOCX files into plain text."""
import os
import re
import tempfile
from pathlib import Path

from backend.app.services.ingestion.document.models import Document


async def load_document(file_bytes: bytes, filename: str) -> Document:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return await _load_pdf(file_bytes, filename)
    if ext == ".docx":
        return await _load_docx(file_bytes, filename)
    raise ValueError(f"Unsupported file type: {ext}. Use .pdf or .docx")


async def _load_pdf(pdf_bytes: bytes, filename: str) -> Document:
    import pdfplumber

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    try:
        page_texts: list[str] = []
        with pdfplumber.open(tmp_path) as pdf:
            total_pages = len(pdf.pages)
            for page in pdf.pages:
                text = page.extract_text(layout=True, x_tolerance=2, y_tolerance=2)
                if text:
                    page_texts.append(text)
                # Drop pdfplumber's per-page parse cache. It otherwise retains every page's
                # chars/layout objects for the life of the open document, ballooning RAM on
                # large PDFs. We never re-read the page, so flushing here is safe.
                page.flush_cache()

        combined = _normalize("\n\n".join(page_texts))
        return Document(
            text=combined,
            metadata={
                "source": filename,
                "document_name": filename,
                "total_pages": total_pages,
            },
        )
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


async def _load_docx(docx_bytes: bytes, filename: str) -> Document:
    import docx as docx_lib

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(docx_bytes)
        tmp_path = tmp.name

    try:
        doc = docx_lib.Document(tmp_path)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        combined = _normalize("\n\n".join(paragraphs))
        return Document(
            text=combined,
            metadata={
                "source": filename,
                "document_name": filename,
                "total_pages": 1,
            },
        )
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _normalize(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return text.strip()
