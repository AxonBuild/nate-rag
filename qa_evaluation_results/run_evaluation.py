"""
RAG Evaluation Script — runs all 40 queries against the chat endpoint
and saves individual MD + raw JSON files per query.

Per-query output:
  <ID>.md        — formatted evaluation report
  <ID>_raw.json  — full raw output: answer, refined_query, keywords, all retrieved chunks
"""
import json
import sys
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

sys.stdout.reconfigure(encoding="utf-8")

API_URL = "http://localhost:8000/chat/"
OUTPUT_DIR = Path(__file__).parent
RAW_DIR = OUTPUT_DIR / "raw"
RAW_DIR.mkdir(exist_ok=True)
WORKERS = 5

_print_lock = threading.Lock()


def safe_print(*args):
    with _print_lock:
        print(*args, flush=True)


def call_api(query: str) -> dict:
    resp = requests.post(API_URL, json={"question": query}, timeout=60)
    resp.raise_for_status()
    return resp.json()


def verdict_for_false(answer: str) -> str:
    deflect_phrases = [
        "don't have enough information",
        "i don't have",
        "not enough information",
        "connect directly",
        "let's connect",
        "speak with",
        "can't answer",
        "no information",
        "outside of",
        "not covered",
    ]
    answer_lower = answer.lower()
    if any(p in answer_lower for p in deflect_phrases):
        return "PASS"
    return "HALLUCINATED"


def analyze(entry: dict, api_response: dict) -> str:
    query_id = entry["id"]
    query = entry["query"]
    ground_truth = entry["ground_truth"]
    expected_source = entry["expected_source"]
    is_false = query_id.startswith("F")

    answer = api_response.get("answer", "")
    results = api_response.get("search", {}).get("results", [])

    # Build retrieved chunks section
    chunks_md = ""
    for i, chunk in enumerate(results[:8], 1):
        score = chunk.get("score", 0)
        doc = chunk.get("document_name", "unknown")
        ftype = chunk.get("file_type", "unknown")
        text = (chunk.get("text") or chunk.get("answer") or "")[:200]
        chunks_md += f"**[{i}]** score={score:.3f} | `{ftype}` | {doc}\n> {text}\n\n"

    # Retrieval analysis
    expected_lower = expected_source.lower()
    found_rank = None
    for i, chunk in enumerate(results[:5], 1):
        doc = (chunk.get("document_name") or "").lower()
        if any(word in doc for word in expected_lower.split() if len(word) > 3):
            found_rank = i
            break

    retrieval_status = f"Yes — rank #{found_rank}" if found_rank else "No — not in top 5"
    top_chunk = results[0] if results else {}
    top_doc = top_chunk.get("document_name", "N/A")
    top_score = top_chunk.get("score", 0)

    # Answer analysis
    if is_false:
        v = verdict_for_false(answer)
        verdict = "✅ Correctly deflected" if v == "PASS" else "🚫 Hallucinated"
        answer_analysis = f"""- **False question handling:** {verdict}
- **Model response:** {"Correctly refused to answer" if v == "PASS" else "Provided an answer when it should have deflected"}"""
    else:
        # Simple keyword overlap check between ground truth and answer
        gt_words = set(ground_truth.lower().split())
        ans_words = set(answer.lower().split())
        overlap = len(gt_words & ans_words) / max(len(gt_words), 1)

        if overlap > 0.3 and found_rank:
            verdict = "✅ Pass"
        elif overlap > 0.15 or found_rank:
            verdict = "⚠️ Partial"
        else:
            verdict = "❌ Fail"

        answer_analysis = f"""- **Ground truth alignment:** {"Strong" if overlap > 0.3 else "Partial" if overlap > 0.15 else "Weak"} (keyword overlap: {overlap:.0%})
- **Expected source retrieved:** {retrieval_status}"""

    md = f"""# Query [{query_id}]

## Query
{query}

## Ground Truth
{ground_truth}

## Expected Source
{expected_source}

## Model Answer
{answer}

## Retrieved Chunks

{chunks_md}
## Retrieval Analysis
- Expected source in top 5: {retrieval_status}
- Top chunk: {top_doc} (score={top_score:.3f})

## Answer Analysis
{answer_analysis}

## Verdict
{verdict}
"""
    return md, verdict


def process_query(entry: dict) -> tuple[str, str]:
    query_id = entry["id"]
    safe_print(f"  [{query_id}] Querying...")
    try:
        api_response = call_api(entry["query"])

        # Save full raw JSON
        search = api_response.get("search", {})
        raw_output = {
            "id": query_id,
            "query": entry["query"],
            "ground_truth": entry["ground_truth"],
            "expected_source": entry["expected_source"],
            "answer": api_response.get("answer", ""),
            "refined_query": search.get("refined_query", ""),
            "original_query": search.get("query", entry["query"]),
            "keywords": search.get("keywords", []),
            "retrieved_chunks": [
                {
                    "rank": i + 1,
                    "score": chunk.get("score"),
                    "document_name": chunk.get("document_name"),
                    "doc_type": chunk.get("doc_type"),
                    "file_type": chunk.get("file_type"),
                    "topic": chunk.get("topic"),
                    "chunk_id": chunk.get("chunk_id"),
                    "text": chunk.get("text", ""),
                    "answer": chunk.get("answer", ""),
                    "tags": chunk.get("tags"),
                    "level": chunk.get("level"),
                }
                for i, chunk in enumerate(search.get("results", []))
            ],
        }
        raw_file = RAW_DIR / f"{query_id}_raw.json"
        raw_file.write_bytes(json.dumps(raw_output, indent=2, ensure_ascii=False).encode("utf-8"))

        # Save MD evaluation
        md, verdict = analyze(entry, api_response)
        out_file = OUTPUT_DIR / f"{query_id}.md"
        out_file.write_bytes(md.encode("utf-8"))

        safe_print(f"  [{query_id}] {verdict} → saved {query_id}.md + {query_id}_raw.json")
        return query_id, verdict
    except Exception as e:
        safe_print(f"  [{query_id}] ERROR: {e}")
        return query_id, "ERROR"


def main():
    queries = json.loads((OUTPUT_DIR / "test_queries.json").read_text(encoding="utf-8"))
    print(f"Running evaluation on {len(queries)} queries with {WORKERS} workers...\n")

    verdicts = {}
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(process_query, entry): entry["id"] for entry in queries}
        for future in as_completed(futures):
            qid, verdict = future.result()
            verdicts[qid] = verdict

    # Summary
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    counts = {}
    for v in verdicts.values():
        counts[v] = counts.get(v, 0) + 1
    for verdict, count in sorted(counts.items()):
        print(f"  {verdict}: {count}")
    print(f"\nTotal: {len(verdicts)} queries evaluated")
    print(f"MD files saved to: {OUTPUT_DIR}")
    print(f"Raw JSON files saved to: {RAW_DIR}")


if __name__ == "__main__":
    main()
