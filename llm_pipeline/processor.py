import json
from pathlib import Path

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
    """Drop groups whose advisor messages are fully contained in an already-seen group."""
    seen: list[frozenset] = []
    unique = []
    for group in groups:
        key = frozenset(group.advisor_messages)
        if not key or not any(key <= s for s in seen):
            unique.append(group)
            if key:
                seen.append(key)
    return unique


def _reconstruct(
    raw_messages: list[dict],
    result: ExtractionResult,
) -> list[QAGroupFull]:
    index_map = {m["index"]: m for m in raw_messages}
    groups = []

    for group in result.qa_groups:
        client_texts = [
            index_map[i]["text"]
            for i in group.client_message_indices
            if i in index_map
        ]
        advisor_texts = [
            index_map[i]["text"]
            for i in group.advisor_message_indices
            if i in index_map
        ]
        groups.append(
            QAGroupFull(
                question=group.question,
                tags=group.tags,
                client_messages=client_texts,
                advisor_messages=advisor_texts,
            )
        )

    return groups


def process_file(input_path: Path, model: str) -> ProcessedChat:
    raw = json.loads(input_path.read_text(encoding="utf-8"))
    client = raw.get("source_file", input_path.stem)
    thread_subject = raw.get("thread_subject", "")

    filtered_messages, filter_stats = filter_messages(raw["messages"])
    filter_stats.log()
    indexed_messages = _index_messages(filtered_messages)
    chunks = _chunk(indexed_messages)

    all_groups: list[QAGroupFull] = []

    for i, chunk in enumerate(chunks, 1):
        print(f"  chunk {i}/{len(chunks)} (msgs {chunk[0]['index']}–{chunk[-1]['index']}) ...", end=" ", flush=True)

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
        result = extract_qa_groups(
            system_prompt=SYSTEM_PROMPT,
            user_message=user_msg,
            model=model,
        )
        groups = _reconstruct(indexed_messages, result)
        all_groups.extend(groups)
        print(f"{len(groups)} groups")

    all_groups = _deduplicate(all_groups)

    return ProcessedChat(
        client=client,
        thread_subject=thread_subject,
        source_file=input_path.name,
        filter_stats=filter_stats.to_dict(),
        qa_groups=all_groups,
    )
