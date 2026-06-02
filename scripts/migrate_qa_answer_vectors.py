"""
Migration: add 'answer_content' (dense) and 'answer_content_sparse' (BM25) vectors
to existing QA pair points in Qdrant.

Each QA point currently has one vector ('content') embedded from the question.
This script adds two more vectors from the answer text:
  - answer_content        : dense semantic vector
  - answer_content_sparse : BM25 sparse vector

This enables 3-way RRF retrieval: question dense + answer dense + answer sparse.

Usage:
    # Dry run — shows what would be updated, no writes
    python -m scripts.migrate_qa_answer_vectors --dry-run

    # Smoke test — update only first 10 unprocessed points
    python -m scripts.migrate_qa_answer_vectors --limit 10

    # Full migration (skips already-updated points by default)
    python -m scripts.migrate_qa_answer_vectors

    # Verify coverage after migration
    python -m scripts.migrate_qa_answer_vectors --verify
"""
import asyncio
import argparse
import logging
import sys
from typing import Optional

from qdrant_client.models import (
    Filter, FieldCondition, MatchValue,
    SparseVector, PointVectors,
    DenseVectorNameConfig, SparseVectorNameConfig,
    DenseVectorConfig, SparseVectorConfig,
    Distance, Modifier,
)

from src.ingestion.embeddings import EmbeddingService
from src.ingestion.qdrant_client import QdrantClient
from src.ingestion.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

ANSWER_DENSE_NAME  = "answer_content"
ANSWER_SPARSE_NAME = "answer_content_sparse"
SCROLL_BATCH = 200   # fetch payload + vectors together in larger pages
EMBED_BATCH  = 100   # points per embedding + update batch


def _qa_filter() -> Filter:
    return Filter(must=[FieldCondition(key="file_type", match=MatchValue(value="qa_pair"))])


def _is_complete(point) -> bool:
    """True if both answer vectors are already present."""
    vecs = point.vector if isinstance(point.vector, dict) else {}
    return (
        bool(vecs.get(ANSWER_DENSE_NAME))
        and bool(vecs.get(ANSWER_SPARSE_NAME))
    )


async def scroll_qa_points(qc: QdrantClient, with_vectors: bool = False):
    """
    Generator: yields pages of QA points one scroll page at a time.
    Fetches payload + (optionally) vectors in a single pass — no second retrieve.
    """
    offset = None
    while True:
        result, next_offset = await asyncio.to_thread(
            qc.client.scroll,
            collection_name=qc.collection_name,
            scroll_filter=_qa_filter(),
            limit=SCROLL_BATCH,
            offset=offset,
            with_payload=True,
            with_vectors=with_vectors,
        )
        yield result
        if next_offset is None:
            break
        offset = next_offset


async def ensure_vector_configs(qc: QdrantClient, vector_size: int) -> None:
    """Add answer_content and answer_content_sparse to collection schema if missing."""
    info = await asyncio.to_thread(
        qc.client.get_collection,
        collection_name=qc.collection_name,
    )
    existing_dense  = info.config.params.vectors or {}
    existing_sparse = info.config.params.sparse_vectors or {}

    if ANSWER_DENSE_NAME not in existing_dense:
        logger.info(f"Adding '{ANSWER_DENSE_NAME}' dense vector config...")
        await asyncio.to_thread(
            qc.client.create_vector_name,
            collection_name=qc.collection_name,
            vector_name=ANSWER_DENSE_NAME,
            vector_name_config=DenseVectorNameConfig(
                dense=DenseVectorConfig(size=vector_size, distance=Distance.COSINE),
            ),
        )

    if ANSWER_SPARSE_NAME not in existing_sparse:
        logger.info(f"Adding '{ANSWER_SPARSE_NAME}' sparse vector config...")
        await asyncio.to_thread(
            qc.client.create_vector_name,
            collection_name=qc.collection_name,
            vector_name=ANSWER_SPARSE_NAME,
            vector_name_config=SparseVectorNameConfig(
                sparse=SparseVectorConfig(modifier=Modifier.IDF),
            ),
        )

    logger.info("Vector configs ready.")


async def run_verify(qc: QdrantClient) -> None:
    """
    Single-pass verify: scrolls with vectors=True, counts coverage inline.
    No second retrieve pass needed.
    """
    logger.info("=== VERIFY ===")
    total = has_both = missing_both = missing_dense = missing_sparse = 0
    sample = []

    async for page in scroll_qa_points(qc, with_vectors=True):
        for p in page:
            total += 1
            vecs = p.vector if isinstance(p.vector, dict) else {}
            d = bool(vecs.get(ANSWER_DENSE_NAME))
            s = bool(vecs.get(ANSWER_SPARSE_NAME))
            if d and s:
                has_both += 1
            elif d:
                missing_sparse += 1
                if len(sample) < 5:
                    sample.append((p.id, "missing sparse"))
            elif s:
                missing_dense += 1
                if len(sample) < 5:
                    sample.append((p.id, "missing dense"))
            else:
                missing_both += 1
                if len(sample) < 5:
                    sample.append((p.id, "missing both"))

    logger.info(f"  Total QA points    : {total}")
    logger.info(f"  Has both vectors   : {has_both}")
    logger.info(f"  Missing dense only : {missing_dense}")
    logger.info(f"  Missing sparse only: {missing_sparse}")
    logger.info(f"  Missing both       : {missing_both}")
    logger.info(f"  Needs update       : {total - has_both}")
    if sample:
        logger.info("  Sample incomplete:")
        for pid, reason in sample:
            logger.info(f"    {pid} ({reason})")


async def run_migration(
    dry_run: bool = False,
    limit: Optional[int] = None,
) -> None:
    logger.info("=== MIGRATION: answer_content + answer_content_sparse ===")
    if dry_run:
        logger.info("DRY RUN — no writes")

    qc = QdrantClient()
    embedding_service = EmbeddingService()

    if not dry_run:
        await ensure_vector_configs(qc, settings.embedding_dimension)

    sparse_model = await qc._get_sparse_model()

    total_seen = total_skipped = total_updated = skipped_no_answer = 0
    pending: list = []   # buffer of incomplete points waiting to form an embed batch

    async def flush(batch: list) -> None:
        """Embed + update a batch of points."""
        nonlocal total_updated, skipped_no_answer

        answers, valid = [], []
        for p in batch:
            answer = (p.payload or {}).get("answer", "").strip()
            if not answer:
                skipped_no_answer += 1
                logger.warning(f"  Skipping {p.id} — empty answer")
                continue
            answers.append(answer)
            valid.append(p)

        if not answers:
            return

        # Embed dense + sparse in parallel
        dense_task   = embedding_service.generate_embeddings_batch(answers)
        sparse_vecs  = list(sparse_model.embed(answers))   # local, instant
        dense_vecs   = await dense_task

        update_points = [
            PointVectors(
                id=pt.id,
                vector={
                    ANSWER_DENSE_NAME: d_emb,
                    ANSWER_SPARSE_NAME: SparseVector(
                        indices=s_emb.indices.tolist(),
                        values=s_emb.values.tolist(),
                    ),
                },
            )
            for pt, d_emb, s_emb in zip(valid, dense_vecs, sparse_vecs)
        ]

        await asyncio.to_thread(
            qc.client.update_vectors,
            collection_name=qc.collection_name,
            points=update_points,
            wait=False,   # fire-and-forget per batch — much faster
        )

        total_updated += len(valid)
        logger.info(f"  Updated {total_updated} points so far...")

    # Single-pass scroll: fetch payload + vectors together
    async for page in scroll_qa_points(qc, with_vectors=True):
        for p in page:
            total_seen += 1

            if _is_complete(p):
                total_skipped += 1
                continue

            pending.append(p)

            if limit is not None and (total_updated + len(pending)) >= limit:
                # Trim pending to not exceed limit
                pending = pending[:limit - total_updated]
                break

            if len(pending) >= EMBED_BATCH:
                if not dry_run:
                    await flush(pending)
                pending = []

        # Break outer loop too if limit reached
        if limit is not None and total_updated >= limit:
            break

    # Flush remainder
    if pending and not dry_run:
        await flush(pending)
    elif pending and dry_run:
        logger.info(f"DRY RUN: would update {len(pending)} more points in final batch")

    logger.info(f"\nDone.")
    logger.info(f"  Scanned          : {total_seen}")
    logger.info(f"  Already complete : {total_skipped}")
    logger.info(f"  Updated          : {total_updated}")
    logger.info(f"  Skipped (empty)  : {skipped_no_answer}")
    if not dry_run:
        logger.info(f"\nRun --verify to confirm final coverage.")


def main():
    parser = argparse.ArgumentParser(
        description="Add answer_content (dense) + answer_content_sparse (BM25) to QA points"
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview only — no writes")
    parser.add_argument("--verify",  action="store_true", help="Report vector coverage (single pass)")
    parser.add_argument("--limit",   type=int, default=None, help="Process only first N unprocessed points")
    args = parser.parse_args()

    async def _main():
        qc = QdrantClient()
        if args.verify:
            await run_verify(qc)
        else:
            await run_migration(dry_run=args.dry_run, limit=args.limit)

    asyncio.run(_main())


if __name__ == "__main__":
    main()
