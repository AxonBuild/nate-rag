"""
Usage:
    python -m llm_pipeline.run [--input parsed_chats] [--output qa_output_v2] [--model openai/gpt-5.1] [--limit N] [--workers N]

Processes every .json file in --input and writes results to --output.
Pass --limit N to process only the top N unprocessed files by message count.
Pass --workers N to process files in parallel (default 1). Recommended: 4-6.
Output folder determines progress tracking: folders containing 'v2' use the processed_v2 column.
"""
import argparse
import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_print_lock = threading.Lock()


def _client_folder(stem: str) -> str:
    """Derive client folder name from filename stem, stripping ', TD Chat' suffix."""
    return stem.removesuffix(", TD Chat").removesuffix(" TD Chat")


def _safe_print(*args, **kwargs) -> None:
    with _print_lock:
        print(*args, **kwargs)


def _process_one(
    path: Path,
    output_dir: Path,
    model: str,
    total: int,
    index: int,
    mark_fn,
    is_v2: bool,
) -> tuple[Path, int | None, Exception | None]:
    """Process a single file. Returns (path, qa_count_or_None, error_or_None)."""
    from llm_pipeline.processor import process_file

    client_dir = output_dir / _client_folder(path.stem)
    client_dir.mkdir(parents=True, exist_ok=True)
    out_path = client_dir / "extraction.json"

    if out_path.exists():
        _safe_print(f"[{index}/{total}] SKIP (already exists): {path.name}")
        return path, None, None

    _safe_print(f"[{index}/{total}] Starting: {path.name}")
    try:
        result = process_file(path, model=model, output_dir=str(output_dir))
        out_path.write_text(
            json.dumps(result.model_dump(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        _safe_print(f"[{index}/{total}] Done: {path.name} ({len(result.qa_groups)} QA groups)")
        n_qa = len(result.qa_groups)
        if is_v2:
            mark_fn(path.name, qa_count=n_qa)
        else:
            mark_fn(path.name)
        return path, n_qa, None
    except Exception as e:
        _safe_print(f"[{index}/{total}] ERROR: {path.name}: {e}")
        return path, None, e


def main():
    parser = argparse.ArgumentParser(description="Extract QA groups from parsed chat files.")
    parser.add_argument("--input", default="parsed_chats", help="Folder with parsed JSON chat files")
    parser.add_argument("--output", default="qa_output_gpt51", help="Folder to write processed QA JSON files")
    parser.add_argument("--model", default="openai/gpt-5.1", help="LLM model identifier")
    parser.add_argument("--file", default=None, help="Process a single file by name (for testing)")
    parser.add_argument("--limit", type=int, default=None, help="Process only the top N unprocessed files by message count")
    parser.add_argument("--workers", type=int, default=1, help="Number of parallel workers (default 1)")
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set in environment or .env file")
        sys.exit(1)

    from llm_pipeline.progress import (
        CSV_PATH, init_csv,
        mark_processed, get_unprocessed,
        mark_processed_v2, get_unprocessed_v2,
        _ensure_v2_columns,
    )

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)

    # Determine if this is a v2 run based on output folder name
    is_v2 = "v2" in output_dir.name.lower()
    mark_fn = mark_processed_v2 if is_v2 else mark_processed

    if not CSV_PATH.exists():
        init_csv(input_dir, output_dir)

    if is_v2:
        _ensure_v2_columns()

    if args.file:
        files = [input_dir / args.file]
    elif args.limit:
        if is_v2:
            files = [input_dir / name for name in get_unprocessed_v2(args.limit, output_dir)]
        else:
            files = [input_dir / name for name in get_unprocessed(args.limit)]
        if not files:
            print("No unprocessed files remaining.")
            sys.exit(0)
    else:
        files = sorted(input_dir.glob("*.json"))

    if not files:
        print(f"No JSON files found in {input_dir}")
        sys.exit(1)

    workers = max(1, args.workers)
    print(f"Processing {len(files)} file(s) with model '{args.model}' | workers={workers} | output={output_dir}")

    if workers == 1:
        for i, path in enumerate(files, 1):
            _process_one(path, output_dir, args.model, len(files), i, mark_fn, is_v2)
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(
                    _process_one, path, output_dir, args.model, len(files), i, mark_fn, is_v2
                ): path
                for i, path in enumerate(files, 1)
            }
            errors = []
            for future in as_completed(futures):
                _, _, err = future.result()
                if err:
                    errors.append((futures[future].name, err))

        if errors:
            print(f"\n{len(errors)} file(s) failed:")
            for name, err in errors:
                print(f"  {name}: {err}")

    print("\nDone.")


if __name__ == "__main__":
    main()
