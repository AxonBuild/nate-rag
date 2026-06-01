"""
Batch ingestion script for KB_TO_PROCESS/.

Walks all files, derives topic + doc_type from folder/filename,
and indexes each document into Qdrant using the hierarchical pipeline.

Usage:
    python -m ingestion.ingest
    python -m ingestion.ingest --dry-run        # print files without ingesting
    python -m ingestion.ingest --file "path"    # ingest single file
"""
import asyncio
import argparse
import logging
import re
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

KB_ROOT = Path(__file__).parent.parent.parent / "KB_TO_PROCESS"

# Maps folder name patterns → clean topic label
TOPIC_MAP = {
    "0 - firm guidelines": "Firm Guidelines",
    "1 - general strategy": "General Strategy",
    "2 - real estate rules": "Real Estate Rules",
    "3 - maximizing deductions": "Maximizing Deductions",
    "4 - the str loophole": "STR Loophole",
    "5 - reps": "REPS",
    "6 - cost segs": "Cost Segs",
    "7 - 1031s": "1031s",
    "8 - entity selection": "Entity Selection",
    "9 - paying children": "Paying Children & Augusta Rule",
    "10 - qozs": "QOZs",
    "11 - s corps": "S Corps",
    "12 - dsts": "DSTs",
    "research": "Research",
    "admin": "Admin",
}


def derive_topic(path: Path) -> str:
    """Derive topic from the advisory folder name in the path."""
    for part in path.parts:
        part_lower = part.lower()
        for key, label in TOPIC_MAP.items():
            if key in part_lower:
                return label
    return "General"


def derive_doc_type(path: Path) -> str:
    """Derive doc_type from filename patterns."""
    name = path.name.lower()
    if path.suffix.lower() == ".pdf":
        return "pdf"
    if "ppt outline" in name or "outline" in name:
        return "outline"
    if name.startswith("seo -") or name.startswith("seo-"):
        return "seo"
    if "script" in name:
        return "script"
    if "research" in name:
        return "research"
    return "guide"


def collect_files(root: Path) -> list[Path]:
    """Collect all ingestible files from KB_TO_PROCESS."""
    supported = {".pdf", ".docx"}
    files = []
    for f in sorted(root.rglob("*")):
        if f.is_file() and f.suffix.lower() in supported:
            files.append(f)
    return files


async def ingest_file(service, path: Path, kb_root: Path) -> dict:
    """Ingest a single file."""
    topic = derive_topic(path)
    doc_type = derive_doc_type(path)
    try:
        rel = path.relative_to(kb_root)
    except ValueError:
        rel = path

    logger.info(f"Ingesting: {rel}  (topic={topic}, doc_type={doc_type})")

    file_bytes = path.read_bytes()
    result = await service.process_and_index_document(
        file_bytes=file_bytes,
        filename=path.name,
        topic=topic,
        doc_type=doc_type,
    )
    logger.info(
        f"  Done: {result['chunks_created']} chunks "
        f"{result.get('chunks_by_level', '')}"
    )
    return result


async def run(dry_run: bool = False, single_file: str | None = None):
    from src.ingestion.document_service import DocumentService

    service = DocumentService()

    if single_file:
        files = [Path(single_file).resolve()]
    else:
        files = collect_files(KB_ROOT)

    logger.info(f"Found {len(files)} files to ingest in {KB_ROOT}")

    if dry_run:
        logger.info("=== DRY RUN — no ingestion ===")
        for f in files:
            rel = f.relative_to(KB_ROOT)
            topic = derive_topic(f)
            doc_type = derive_doc_type(f)
            print(f"  {rel}  ->  topic={topic}  doc_type={doc_type}")
        return

    results = []
    failed = []

    for i, path in enumerate(files, 1):
        logger.info(f"[{i}/{len(files)}] {path.name}")
        try:
            result = await ingest_file(service, path, KB_ROOT)
            results.append(result)
        except Exception as e:
            logger.error(f"  FAILED: {path.name} — {e}", exc_info=True)
            failed.append({"file": str(path), "error": str(e)})

    # Summary
    total_chunks = sum(r.get("chunks_created", 0) for r in results)
    logger.info(f"\n{'='*50}")
    logger.info(f"Ingestion complete:")
    logger.info(f"  Files processed: {len(results)}/{len(files)}")
    logger.info(f"  Total chunks indexed: {total_chunks}")
    if failed:
        logger.warning(f"  Failed: {len(failed)}")
        for f in failed:
            logger.warning(f"    {f['file']}: {f['error']}")


def main():
    parser = argparse.ArgumentParser(description="Ingest KB_TO_PROCESS documents into Qdrant")
    parser.add_argument("--dry-run", action="store_true", help="Print files without ingesting")
    parser.add_argument("--file", type=str, default=None, help="Ingest a single file by path")
    args = parser.parse_args()
    asyncio.run(run(dry_run=args.dry_run, single_file=args.file))


if __name__ == "__main__":
    main()
