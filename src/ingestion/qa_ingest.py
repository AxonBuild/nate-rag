"""
Ingest QA pairs from qa_output_v2 (chat) and transcript_output (transcripts) into Qdrant.
Embeds the question, stores full answer + metadata as payload.

Usage:
    python -m ingestion.qa_ingest
    python -m ingestion.qa_ingest --dry-run
    python -m ingestion.qa_ingest --source transcripts   # only transcripts
    python -m ingestion.qa_ingest --source chats         # only chat QA
"""
import asyncio
import argparse
import json
import logging
import sys
import uuid
from pathlib import Path

from src.ingestion.embeddings import EmbeddingService
from src.ingestion.qdrant_client import QdrantClient
from src.ingestion.config import settings
from qdrant_client.models import (
    PointStruct, Filter, FieldCondition, MatchValue, PayloadSchemaType
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

CHAT_ROOT = Path(__file__).parent.parent.parent / "qa_output_v2"
TRANSCRIPT_ROOT = Path(__file__).parent.parent.parent / "transcript_output"


def stable_id(source: str, client: str, index: int) -> str:
    key = f"{source}_qa_{client}_{index}"
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, key))


def collect_chat_pairs(root: Path) -> list[dict]:
    """Collect QA pairs from qa_output_v2/**/extraction.json files."""
    pairs = []
    for f in sorted(root.rglob("extraction.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Could not read {f}: {e}")
            continue
        client = data.get("client", f.parent.name)
        for i, qa in enumerate(data.get("qa_groups", [])):
            question = qa.get("question", "").strip()
            answer = qa.get("answer", "").strip()
            if not question or not answer:
                continue
            pairs.append({
                "chunk_id": f"chat_qa_{client}_{i}",
                "point_id": stable_id("chat", client, i),
                "text": question,
                "answer": answer,
                "tags": qa.get("tags", []),
                "reasoning": qa.get("reasoning", ""),
                "document_name": client,
                "source": "chat",
                "doc_type": "qa_pair",
                "file_type": "qa_pair",
                "topic": None,
                "level": None,
                "parent_id": None,
                "prev_chunk": None,
                "next_chunk": None,
                "page_number": None,
            })
    return pairs


def collect_transcript_pairs(root: Path) -> list[dict]:
    """Collect QA pairs from transcript_output/*.json files."""
    pairs = []
    for f in sorted(root.glob("*.json")):
        try:
            data = json.loads(f.read_bytes().decode("utf-8"))
        except Exception as e:
            logger.warning(f"Could not read {f}: {e}")
            continue
        client = data.get("client", f.stem)
        meeting_date = data.get("meeting_date", "")
        for i, qa in enumerate(data.get("qa_groups", [])):
            question = qa.get("question", "").strip()
            answer = qa.get("answer", "").strip()
            if not question or not answer:
                continue
            pairs.append({
                "chunk_id": f"transcript_qa_{client}_{i}",
                "point_id": stable_id("transcript", client, i),
                "text": question,
                "answer": answer,
                "tags": qa.get("tags", []),
                "reasoning": qa.get("reasoning", ""),
                "document_name": client,
                "meeting_date": meeting_date,
                "source": "transcript",
                "doc_type": "qa_pair",
                "file_type": "qa_pair",
                "topic": None,
                "level": None,
                "parent_id": None,
                "prev_chunk": None,
                "next_chunk": None,
                "page_number": None,
            })
    return pairs


def collect_all_pairs(source_filter: str | None) -> list[dict]:
    pairs = []
    if source_filter != "transcripts":
        chat_pairs = collect_chat_pairs(CHAT_ROOT)
        logger.info(f"Found {len(chat_pairs)} QA pairs from chats (qa_output_v2)")
        pairs.extend(chat_pairs)
    if source_filter != "chats":
        transcript_pairs = collect_transcript_pairs(TRANSCRIPT_ROOT)
        logger.info(f"Found {len(transcript_pairs)} QA pairs from transcripts")
        pairs.extend(transcript_pairs)
    return pairs


async def ensure_tags_index(qc: QdrantClient) -> None:
    try:
        await asyncio.to_thread(
            qc.client.create_payload_index,
            collection_name=qc.collection_name,
            field_name="tags",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        logger.info("Created payload index: tags")
    except Exception as e:
        if "already" not in str(e).lower():
            logger.warning(f"Could not create tags index: {e}")


async def run(dry_run: bool = False, source_filter: str | None = None):
    pairs = collect_all_pairs(source_filter)
    logger.info(f"Total QA pairs to ingest: {len(pairs)}")

    if dry_run:
        logger.info("=== DRY RUN ===")
        by_source: dict[str, dict[str, int]] = {}
        for p in pairs:
            src = p["source"]
            by_source.setdefault(src, {})
            by_source[src][p["document_name"]] = by_source[src].get(p["document_name"], 0) + 1
        for src, clients in sorted(by_source.items()):
            print(f"\n[{src}]")
            for client, count in sorted(clients.items()):
                print(f"  {client}: {count} pairs")
        print(f"\nTotal: {len(pairs)} pairs")
        return

    embedding_service = EmbeddingService()
    qc = QdrantClient()

    await asyncio.to_thread(qc.client.get_collections)
    await ensure_tags_index(qc)

    questions = [p["text"] for p in pairs]
    logger.info(f"Embedding {len(questions)} questions...")
    embeddings = await embedding_service.generate_embeddings_batch(questions)
    logger.info("Embeddings done.")

    points = []
    for pair, emb in zip(pairs, embeddings):
        payload = {k: v for k, v in pair.items() if k != "point_id"}
        points.append(PointStruct(
            id=pair["point_id"],
            vector={"content": emb},
            payload=payload,
        ))

    batch_size = 100
    total = 0
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        await asyncio.to_thread(
            qc.client.upsert,
            collection_name=qc.collection_name,
            points=batch,
        )
        total += len(batch)
        logger.info(f"Upserted {total}/{len(points)} QA points")

    logger.info(f"\nDone. {len(points)} QA pairs indexed into '{qc.collection_name}'")


def main():
    parser = argparse.ArgumentParser(description="Ingest QA pairs into Qdrant")
    parser.add_argument("--dry-run", action="store_true", help="Print pairs without ingesting")
    parser.add_argument("--source", choices=["chats", "transcripts"], default=None,
                        help="Ingest only one source (default: both)")
    args = parser.parse_args()
    asyncio.run(run(dry_run=args.dry_run, source_filter=args.source))


if __name__ == "__main__":
    main()
