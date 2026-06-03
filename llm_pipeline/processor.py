import json
from pathlib import Path

from llm_pipeline.cost_tracker import log_run
from llm_pipeline.filters import filter_messages
from llm_pipeline.llm_client.client import extract_qa_groups
from llm_pipeline.prompts.qa_extraction import SYSTEM_PROMPT, build_user_message
from llm_pipeline.schemas import ExtractionResult, ProcessedChat, QAGroupFull

CHUNK_SIZE = 50
OVERLAP = 6


def _index_messages(messages: list[dict]) -> list[dict]:
    return [{"index": i, **m} for i, m in enumerate(messages)]


def _chunk(messages: list[dict]) -> list[list[dict]]:
    chunks = []
    step = CHUNK_SIZE - OVERLAP
    for start in range(0, len(messages), step):
        chunks.append(messages[start : start + CHUNK_SIZE])
        if start + CHUNK_SIZE >= len(messages):
            break
    return chunks


def _deduplicate(groups: list[QAGroupFull]) -> list[QAGroupFull]:
    """Drop groups with identical questions (case-insensitive) already seen."""
    seen: set[str] = set()
    unique = []
    for group in groups:
        key = group.question.strip().lower()
        if key not in seen:
            unique.append(group)
            seen.add(key)
    return unique


def _reconstruct(result: ExtractionResult) -> list[QAGroupFull]:
    groups = []
    for group in result.qa_groups:
        if not group.advisor_message_indices or not group.answer.strip():
            continue
        groups.append(QAGroupFull(
            question=group.question,
            tags=group.tags,
            reasoning=group.reasoning,
            answer=group.answer,
            advisor_message_indices=group.advisor_message_indices,
        ))
    return groups


def process_file(input_path: Path, model: str, output_dir: str = "") -> ProcessedChat:
    raw = json.loads(input_path.read_text(encoding="utf-8"))
    client = raw.get("source_file", input_path.stem)
    thread_subject = raw.get("thread_subject", "")

    filtered_messages, filter_stats = filter_messages(raw["messages"])
    filter_stats.log()
    indexed_messages = _index_messages(filtered_messages)
    chunks = _chunk(indexed_messages)

    all_groups: list[QAGroupFull] = []
    total_input_tokens = 0
    total_output_tokens = 0
    total_cost = 0.0

    for i, chunk in enumerate(chunks, 1):
        print(f"  chunk {i}/{len(chunks)} (msgs {chunk[0]['index']}-{chunk[-1]['index']}) ...", end=" ", flush=True)

        prior = [
            {"question": g.question, "tags": g.tags}
            for g in all_groups[-2:]
        ] or None

        user_msg = build_user_message(
            client=client,
            thread_subject=thread_subject,
            messages=chunk,
            prior_qa_groups=prior,
        )
        response = extract_qa_groups(
            system_prompt=SYSTEM_PROMPT,
            user_message=user_msg,
            model=model,
        )
        groups = _reconstruct(response.result)
        all_groups.extend(groups)
        total_input_tokens += response.input_tokens
        total_output_tokens += response.output_tokens
        total_cost += response.cost
        print(f"{len(groups)} groups")

    all_groups = _deduplicate(all_groups)

    log_run(
        source_file=input_path.name,
        model=model,
        chunks=len(chunks),
        input_tokens=total_input_tokens,
        output_tokens=total_output_tokens,
        cost_usd=total_cost,
        qa_groups=len(all_groups),
        run_type="extraction",
        output_dir=output_dir,
    )
    print(f"  cost: ${total_cost:.4f}  ({total_input_tokens:,} in / {total_output_tokens:,} out tokens)")

    return ProcessedChat(
        client=client,
        thread_subject=thread_subject,
        source_file=input_path.name,
        filter_stats=filter_stats.to_dict(),
        qa_groups=all_groups,
    )
