import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from backend.app.controllers.ingest_controller import IngestController
from backend.app.dependencies.container import (
    get_document_ingest_service,
    get_qa_ingest_service,
    get_transcript_ingest_service,
)
from backend.app.infrastructure.clerk.auth import require_user
from backend.app.schemas.ingest import (
    DeleteDocumentResponse,
    DocumentIngestResponse,
    DocumentListItem,
    QaColumnsPreviewResponse,
    QaIngestResponse,
    TranscriptIngestResponse,
)
from backend.app.services.ingestion.document_ingest_service import DocumentIngestService
from backend.app.services.ingestion.qa_ingest_service import QaIngestService
from backend.app.services.ingestion.transcript_ingest_service import TranscriptIngestService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingest"])

MAX_TRANSCRIPT_BYTES = 25 * 1024 * 1024  # 25 MB
MAX_QA_SPREADSHEET_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_DOCUMENT_BYTES = 25 * 1024 * 1024  # 25 MB


def get_ingest_controller(
    transcript_service: TranscriptIngestService = Depends(get_transcript_ingest_service),
    qa_service: QaIngestService = Depends(get_qa_ingest_service),
    document_service: DocumentIngestService = Depends(get_document_ingest_service),
) -> IngestController:
    return IngestController(transcript_service, qa_service, document_service)


@router.post("/transcript", response_model=TranscriptIngestResponse)
async def ingest_transcript(
    transcript: UploadFile = File(..., description="Fireflies transcript.json"),
    metadata: UploadFile = File(
        ...,
        description="Required meeting-metadata file (meeting-metadata-*.txt JSON from Fireflies)",
    ),
    client_name: str | None = Form(None, description="Client display name"),
    ingest_to_qdrant: bool = Form(True, description="Upsert extracted QA pairs into Qdrant"),
    model: str | None = Form(None, description="Override LLM model for QA extraction"),
    _user: dict[str, str] = Depends(require_user),
    controller: IngestController = Depends(get_ingest_controller),
):
    """
    Upload Fireflies `transcript.json` plus `meeting-metadata-*.txt`, extract QA via LLM,
    optionally index to Qdrant.

    The transcript JSON must contain a top-level `data` array with utterance objects
    (`index`, `speaker_name`, `time`, `sentence`).
    """
    if not transcript.filename or not transcript.filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="Transcript file must be a .json file")
    if not metadata.filename:
        raise HTTPException(status_code=400, detail="Metadata file is required")

    transcript_bytes = await transcript.read()
    if not transcript_bytes:
        raise HTTPException(status_code=400, detail="Transcript file is empty")
    if len(transcript_bytes) > MAX_TRANSCRIPT_BYTES:
        raise HTTPException(status_code=400, detail="Transcript file exceeds 25 MB limit")

    metadata_bytes = await metadata.read()
    if not metadata_bytes:
        raise HTTPException(status_code=400, detail="Metadata file is empty")

    try:
        return await controller.ingest_transcript(
            transcript_bytes,
            metadata_bytes=metadata_bytes,
            client_name=client_name.strip() if client_name else None,
            ingest_to_qdrant=ingest_to_qdrant,
            model=model.strip() if model else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("[ingest] transcript failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Transcript processing failed. Check server logs for details.",
        ) from e


@router.post("/qa/preview", response_model=QaColumnsPreviewResponse)
async def preview_qa_columns(
    file: UploadFile = File(..., description="CSV or XLSX to read column headers from"),
    _user: dict[str, str] = Depends(require_user),
    controller: IngestController = Depends(get_ingest_controller),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File is required")
    lower = file.filename.lower()
    if not (lower.endswith(".csv") or lower.endswith(".xlsx") or lower.endswith(".xlsm")):
        raise HTTPException(status_code=400, detail="File must be .csv or .xlsx")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="File is empty")
    if len(raw) > MAX_QA_SPREADSHEET_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 10 MB limit")

    try:
        return controller.preview_qa_columns(raw, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/qa", response_model=QaIngestResponse)
async def ingest_qa_spreadsheet(
    file: UploadFile = File(..., description="CSV or XLSX with question/answer columns"),
    question_column: str = Form(..., description="Header name for the question column"),
    answer_column: str = Form(..., description="Header name for the answer column"),
    tags_column: str | None = Form(None, description="Optional tags column (comma/semicolon separated)"),
    document_name_column: str | None = Form(
        None,
        description="Optional column for document/client name per row",
    ),
    default_document_name: str = Form(
        "Unknown",
        description="Used when document_name_column is missing or empty",
    ),
    ingest_to_qdrant: bool = Form(True, description="Upsert rows into Qdrant"),
    _user: dict[str, str] = Depends(require_user),
    controller: IngestController = Depends(get_ingest_controller),
):
    """
    Upload a CSV or XLSX and map columns to ingest QA pairs.

    Each valid row is upserted with a stable id from normalized question+answer (re-upload updates in place).
    Rows with an empty question or answer are skipped.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="File is required")
    lower = file.filename.lower()
    if not (lower.endswith(".csv") or lower.endswith(".xlsx") or lower.endswith(".xlsm")):
        raise HTTPException(status_code=400, detail="File must be .csv or .xlsx")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="File is empty")
    if len(raw) > MAX_QA_SPREADSHEET_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 10 MB limit")

    try:
        return await controller.ingest_qa_spreadsheet(
            raw,
            file.filename,
            question_column=question_column.strip(),
            answer_column=answer_column.strip(),
            tags_column=tags_column.strip() if tags_column else None,
            document_name_column=document_name_column.strip()
            if document_name_column
            else None,
            default_document_name=default_document_name.strip() or "Unknown",
            ingest_to_qdrant=ingest_to_qdrant,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("[ingest] qa spreadsheet failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="QA ingest failed. Check server logs for details.",
        ) from e


@router.post("/document", response_model=DocumentIngestResponse)
async def ingest_document(
    file: UploadFile = File(..., description="PDF or DOCX knowledge-base document"),
    document_name: str | None = Form(
        None,
        description="Display name in Qdrant (defaults to filename)",
    ),
    topic: str | None = Form(
        None,
        description='Advisory topic e.g. "STR Loophole", "Cost Segs"',
    ),
    doc_type: str | None = Form(
        None,
        description='Document type e.g. "guide", "script", "seo", "outline"',
    ),
    ingest_to_qdrant: bool = Form(True, description="Embed and upsert chunks into Qdrant"),
    _user: dict[str, str] = Depends(require_user),
    controller: IngestController = Depends(get_ingest_controller),
):
    """
    Upload a PDF or DOCX, extract text, hierarchical chunk (page → paragraph → content),
    embed, and index as `file_type=normal` chunks for KB search.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="File is required")
    lower = file.filename.lower()
    if not (lower.endswith(".pdf") or lower.endswith(".docx")):
        raise HTTPException(status_code=400, detail="File must be .pdf or .docx")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="File is empty")
    if len(raw) > MAX_DOCUMENT_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 25 MB limit")

    try:
        return await controller.ingest_document(
            raw,
            file.filename,
            document_name=document_name.strip() if document_name else None,
            topic=topic.strip() if topic else None,
            doc_type=doc_type.strip() if doc_type else None,
            ingest_to_qdrant=ingest_to_qdrant,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("[ingest] document failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Document ingest failed. Check server logs for details.",
        ) from e


@router.get("/documents", response_model=list[DocumentListItem])
async def list_documents(
    _user: dict[str, str] = Depends(require_user),
    controller: IngestController = Depends(get_ingest_controller),
):
    """List ingested knowledge-base documents (grouped by document, with chunk counts)."""
    return await controller.list_documents()


@router.delete("/documents/{document_id}", response_model=DeleteDocumentResponse)
async def delete_document(
    document_id: str,
    _user: dict[str, str] = Depends(require_user),
    controller: IngestController = Depends(get_ingest_controller),
):
    """Delete every chunk for a document by its document_id."""
    return await controller.delete_document(document_id)
