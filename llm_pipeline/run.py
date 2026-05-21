"""
Usage:
    python -m llm_pipeline.run [--input parsed_chats] [--output qa_output] [--model openai/gpt-4o-mini]

Processes every .json file in --input and writes results to --output.
"""
import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Extract QA groups from parsed chat files.")
    parser.add_argument("--input", default="parsed_chats", help="Folder with parsed JSON chat files")
    parser.add_argument("--output", default="qa_output", help="Folder to write processed QA JSON files")
    parser.add_argument("--model", default="openai/gpt-4o-mini", help="LLM model identifier")
    parser.add_argument("--file", default=None, help="Process a single file by name (for testing)")
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set in environment or .env file")
        sys.exit(1)

    # late import so env is loaded first
    from llm_pipeline.processor import process_file

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)

    files = [Path(args.file)] if args.file else sorted(input_dir.glob("*.json"))

    if not files:
        print(f"No JSON files found in {input_dir}")
        sys.exit(1)

    print(f"Processing {len(files)} file(s) with model '{args.model}'")

    for i, path in enumerate(files, 1):
        out_path = output_dir / path.name
        if out_path.exists():
            print(f"[{i}/{len(files)}] SKIP (already exists): {path.name}")
            continue

        print(f"[{i}/{len(files)}] Processing: {path.name} ...", end=" ", flush=True)
        try:
            result = process_file(path, model=args.model)
            out_path.write_text(
                json.dumps(result.model_dump(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            print(f"done ({len(result.qa_groups)} QA groups)")
        except Exception as e:
            print(f"ERROR: {e}")


if __name__ == "__main__":
    main()
