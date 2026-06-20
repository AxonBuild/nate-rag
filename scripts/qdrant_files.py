"""
List, delete, and date-backfill ingested "files" (documents) in the Qdrant collection.

A "file" is a group of points that share a document — KB documents are grouped by
`document_id`, QA-pair batches are grouped by `document_name` (the client). Use this
to inspect what's been ingested, remove a test upload, or backfill recency dates onto
points that were ingested before `ingested_at` existed.

This script is self-contained: it talks to Qdrant directly and only needs the
`qdrant-client` package (already in requirements.txt). It reads the SAME connection
settings the app uses, from environment variables:

    QDRANT_URL              e.g. https://xxxx.cloud.qdrant.io:6333   (preferred)
    QDRANT_API_KEY          your Qdrant API key
    QDRANT_COLLECTION_NAME  defaults to "nate-rag-docs"
    QDRANT_HOST/PORT/HTTPS  fallback if QDRANT_URL is not set

`scripts/` is not bundled into the production image, so run this from your machine
pointed at the prod Qdrant (it's reachable over the network):

    # List everything in the collection
    QDRANT_URL="https://xxxx.cloud.qdrant.io:6333" QDRANT_API_KEY="…" \
        python scripts/qdrant_files.py list

    # Delete your test file by name (deletes all its chunks)
    QDRANT_URL="…" QDRANT_API_KEY="…" \
        python scripts/qdrant_files.py delete --name "my_test_file.pdf"

    # Or delete by document id (copy it from the `list` output)
    QDRANT_URL="…" QDRANT_API_KEY="…" \
        python scripts/qdrant_files.py delete --id 3f2a…uuid

    # Skip the confirmation prompt
    … delete --name "my_test_file.pdf" --yes

    # Backfill recency dates onto legacy points (DRY RUN — shows what it would do)
    QDRANT_URL="…" QDRANT_API_KEY="…" \
        python scripts/qdrant_files.py backfill-dates

    # Apply it: transcript Q&A gets its meeting_date, everything else gets 2026-06-10
    QDRANT_URL="…" QDRANT_API_KEY="…" \
        python scripts/qdrant_files.py backfill-dates --apply --yes

You can also keep the values in a .env file and pass --env-file path/to/.env.
"""
import argparse
import os
import sys

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
    FilterSelector,
)

DEFAULT_COLLECTION = "nate-rag-docs"
DEFAULT_BACKFILL_DATE = "2026-06-10"
SCROLL_BATCH = 500
SET_PAYLOAD_BATCH = 500


def load_env_file(path: str | None) -> None:
    """Minimal .env loader — only fills vars that aren't already set in the environment."""
    if not path:
        return
    if not os.path.isfile(path):
        print(f"[warn] --env-file not found: {path}", file=sys.stderr)
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def make_client() -> QdrantClient:
    url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")
    timeout = int(os.getenv("QDRANT_TIMEOUT", "120"))
    if url:
        return QdrantClient(url=url, api_key=api_key, timeout=timeout)
    host = os.getenv("QDRANT_HOST")
    if not host:
        print(
            "Error: set QDRANT_URL (or QDRANT_HOST) so the script knows which Qdrant to hit.\n"
            "Example:\n"
            '  QDRANT_URL="https://xxxx.cloud.qdrant.io:6333" QDRANT_API_KEY="…" '
            "python scripts/qdrant_files.py list",
            file=sys.stderr,
        )
        sys.exit(2)
    port = int(os.getenv("QDRANT_PORT", "6333"))
    https = os.getenv("QDRANT_HTTPS", "false").lower() in ("1", "true", "yes")
    return QdrantClient(host=host, port=port, https=https, api_key=api_key, timeout=timeout)


def collection_name() -> str:
    return os.getenv("QDRANT_COLLECTION_NAME", DEFAULT_COLLECTION)


def target_label() -> str:
    return os.getenv("QDRANT_URL") or os.getenv("QDRANT_HOST", "localhost")


def scroll_all(client: QdrantClient, collection: str):
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=collection,
            limit=SCROLL_BATCH,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        for p in points:
            yield p
        if offset is None:
            break


def cmd_list(client: QdrantClient, collection: str) -> None:
    groups: dict[str, dict] = {}
    total_points = 0

    for p in scroll_all(client, collection):
        total_points += 1
        payload = p.payload or {}
        doc_id = payload.get("document_id")
        name = payload.get("document_name") or "(unnamed)"
        ftype = payload.get("file_type") or "?"
        # KB docs key by document_id; QA pairs have no document_id, so key by name+type.
        key = f"id::{doc_id}" if doc_id else f"name::{ftype}::{name}"
        g = groups.setdefault(
            key,
            {"document_id": doc_id, "name": name, "file_type": ftype, "count": 0, "as_of": ""},
        )
        g["count"] += 1
        as_of = str(payload.get("meeting_date") or payload.get("ingested_at") or "")[:10]
        if as_of > g["as_of"]:
            g["as_of"] = as_of

    if not groups:
        print(f"Collection '{collection}' on {target_label()} has no points.")
        return

    rows = sorted(groups.values(), key=lambda g: (g["file_type"], g["name"].lower()))
    print(f"\nCollection: {collection}   ({target_label()})")
    print(f"{len(rows)} file(s), {total_points} total points\n")
    for i, g in enumerate(rows, 1):
        as_of = g["as_of"] or "—"
        print(f"[{i}] {g['name']}")
        print(f"      type={g['file_type']}  chunks={g['count']}  updated={as_of}")
        print(f"      document_id: {g['document_id'] or '— (QA pairs — delete by --name)'}")
    print(
        "\nDelete a file with:\n"
        '  python scripts/qdrant_files.py delete --name "<name>"\n'
        "  python scripts/qdrant_files.py delete --id <document_id>"
    )


def cmd_delete(
    client: QdrantClient,
    collection: str,
    document_id: str | None,
    name: str | None,
    file_type: str | None,
    yes: bool,
) -> None:
    must = []
    described = []
    if document_id:
        must.append(FieldCondition(key="document_id", match=MatchValue(value=document_id)))
        described.append(f"document_id={document_id}")
    if name:
        must.append(FieldCondition(key="document_name", match=MatchValue(value=name)))
        described.append(f"name={name!r}")
    if file_type:
        must.append(FieldCondition(key="file_type", match=MatchValue(value=file_type)))
        described.append(f"file_type={file_type!r}")

    if not must:
        print("Refusing to delete without a selector. Pass --id and/or --name.", file=sys.stderr)
        sys.exit(2)

    flt = Filter(must=must)
    count = client.count(collection_name=collection, count_filter=flt, exact=True).count
    selector = " AND ".join(described)
    if count == 0:
        print(f"No points match {selector} in '{collection}'. Nothing to delete.")
        return

    print(f"This will permanently delete {count} point(s) matching {selector}")
    print(f"from collection '{collection}' on {target_label()}.")
    if not yes:
        confirm = input("Type 'yes' to confirm: ").strip().lower()
        if confirm != "yes":
            print("Aborted.")
            return

    client.delete(collection_name=collection, points_selector=FilterSelector(filter=flt))
    print(f"Deleted {count} point(s).")


def _valid_ymd(s: str) -> bool:
    parts = s.split("-")
    if len(parts) != 3:
        return False
    y, m, d = parts
    return (
        y.isdigit() and len(y) == 4
        and m.isdigit() and len(m) == 2 and 1 <= int(m) <= 12
        and d.isdigit() and len(d) == 2 and 1 <= int(d) <= 31
    )


def _iso_midnight(date_str: str) -> str:
    return f"{date_str}T00:00:00+00:00"


def _meeting_date_ts(raw) -> str | None:
    """Normalize a stored meeting_date ("YYYY-MM-DD…") to an ISO timestamp, or None if unusable."""
    s = str(raw or "").strip()[:10]
    return _iso_midnight(s) if _valid_ymd(s) else None


def cmd_backfill(
    client: QdrantClient,
    collection: str,
    date_str: str,
    apply: bool,
    yes: bool,
    force: bool,
) -> None:
    if not _valid_ymd(date_str):
        print(f"Invalid --date {date_str!r}; expected YYYY-MM-DD.", file=sys.stderr)
        sys.exit(2)
    default_ts = _iso_midnight(date_str)

    buckets: dict[str, list] = {}  # ingested_at value -> point ids to set it on
    total = skipped_existing = meeting_count = default_count = 0

    for p in scroll_all(client, collection):
        total += 1
        payload = p.payload or {}
        if payload.get("ingested_at") and not force:
            skipped_existing += 1
            continue
        md_ts = _meeting_date_ts(payload.get("meeting_date"))
        if md_ts:
            meeting_count += 1
            target = md_ts
        else:
            default_count += 1
            target = default_ts
        buckets.setdefault(target, []).append(p.id)

    to_set = sum(len(ids) for ids in buckets.values())

    print(f"\nCollection: {collection}   ({target_label()})")
    print(f"Scanned {total} point(s).")
    skip_note = "  [re-run with --force to overwrite]" if skipped_existing and not force else ""
    print(f"  Already have ingested_at (skipped): {skipped_existing}{skip_note}")
    print(f"  Meeting chunks -> their meeting_date: {meeting_count}")
    print(f"  Other points   -> {date_str}: {default_count}")
    if buckets:
        print("\n  Dates to be written:")
        for value in sorted(buckets):
            print(f"    {value[:10]}  ->  {len(buckets[value])} point(s)")

    if to_set == 0:
        print("\nNothing to backfill.")
        return

    if not apply:
        print(
            f"\nDRY RUN — nothing written. Re-run with --apply to set ingested_at "
            f"on {to_set} point(s)."
        )
        return

    print(f"\nThis will write ingested_at on {to_set} point(s) in '{collection}' on {target_label()}.")
    if not yes:
        confirm = input("Type 'yes' to apply: ").strip().lower()
        if confirm != "yes":
            print("Aborted.")
            return

    written = 0
    for value, ids in buckets.items():
        for i in range(0, len(ids), SET_PAYLOAD_BATCH):
            chunk = ids[i:i + SET_PAYLOAD_BATCH]
            client.set_payload(
                collection_name=collection,
                payload={"ingested_at": value},
                points=chunk,
                wait=True,
            )
            written += len(chunk)
            print(f"  set {written}/{to_set}…")
    print(f"Done. Set ingested_at on {written} point(s).")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List, delete, and date-backfill ingested files (documents) in Qdrant.",
    )
    # Shared option so `--env-file` works on each subcommand (after the subcommand name).
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--env-file", help="Path to a .env file with QDRANT_* values")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", parents=[common], help="List all files (documents) in the collection")

    d = sub.add_parser("delete", parents=[common], help="Delete all points for a document")
    d.add_argument("--id", dest="document_id", help="Delete by document_id (KB documents)")
    d.add_argument("--name", dest="name", help="Delete by document_name (KB docs or QA client)")
    d.add_argument(
        "--file-type",
        dest="file_type",
        help='Optional: restrict to a file_type ("normal" or "qa_pair")',
    )
    d.add_argument("--yes", action="store_true", help="Skip the confirmation prompt")

    b = sub.add_parser(
        "backfill-dates",
        parents=[common],
        help="Set ingested_at on points that lack it (meeting chunks use their meeting_date)",
    )
    b.add_argument(
        "--date",
        default=DEFAULT_BACKFILL_DATE,
        help=f"Date for non-meeting points (YYYY-MM-DD, default {DEFAULT_BACKFILL_DATE})",
    )
    b.add_argument("--apply", action="store_true", help="Actually write (default is a dry run)")
    b.add_argument("--yes", action="store_true", help="Skip the confirmation prompt")
    b.add_argument(
        "--force", action="store_true", help="Overwrite ingested_at even if already set"
    )

    args = parser.parse_args()
    load_env_file(args.env_file)

    client = make_client()
    collection = collection_name()

    try:
        if args.command == "list":
            cmd_list(client, collection)
        elif args.command == "delete":
            cmd_delete(
                client,
                collection,
                document_id=args.document_id,
                name=args.name,
                file_type=args.file_type,
                yes=args.yes,
            )
        elif args.command == "backfill-dates":
            cmd_backfill(
                client,
                collection,
                date_str=args.date,
                apply=args.apply,
                yes=args.yes,
                force=args.force,
            )
    except Exception as e:  # noqa: BLE001 — surface a clean message for a one-off admin tool
        msg = str(e)
        if "Not found" in msg or "doesn't exist" in msg or "404" in msg:
            print(
                f"Error: collection '{collection}' not found on {target_label()}.\n"
                "Check QDRANT_COLLECTION_NAME / QDRANT_URL.",
                file=sys.stderr,
            )
        else:
            print(f"Error talking to Qdrant: {msg}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
