"""Utterance loading, chunking, and LLM user-message building."""
import json
from pathlib import Path

CHUNK_SIZE = 200
OVERLAP = 30
STEP = CHUNK_SIZE - OVERLAP

_PROMPT_PATH = Path(__file__).parent / "prompts" / "transcript_qa_extraction.md"


def get_system_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def detect_advisor(utterances: list[dict]) -> str:
    """Return the speaker name containing 'CPA' — falls back to first speaker."""
    for u in utterances:
        name = u.get("speaker_name", "")
        if "CPA" in name:
            return name
    return utterances[0]["speaker_name"] if utterances else "Advisor"


def load_utterances(transcript_json: dict) -> list[dict]:
    """Parse Fireflies transcript.json `data` array into normalized utterances."""
    return [
        {
            "index": u["index"],
            "speaker_name": u["speaker_name"],
            "time": u["time"],
            "sentence": u["sentence"],
        }
        for u in (transcript_json.get("data") or [])
    ]


def estimate_duration_minutes(utterances: list[dict]) -> int:
    if not utterances:
        return 0
    last_seconds = float(utterances[-1].get("time") or 0)
    return max(1, int(last_seconds // 60) + 1)


def _format_utterance(u: dict) -> str:
    minutes = int(u["time"] // 60)
    seconds = int(u["time"] % 60)
    return f"[{minutes:02d}:{seconds:02d}] ({u['index']}) {u['speaker_name']}: {u['sentence']}"


def chunk_utterances(utterances: list[dict]) -> list[list[dict]]:
    chunks: list[list[dict]] = []
    start = 0
    while start < len(utterances):
        chunks.append(utterances[start : start + CHUNK_SIZE])
        if start + CHUNK_SIZE >= len(utterances):
            break
        start += STEP
    return chunks


def build_user_message(
    meeting_title: str,
    meeting_date: str,
    duration_minutes: int,
    utterances: list[dict],
    advisor_name: str,
    prior_qa_groups: list[dict] | None = None,
) -> str:
    payload: dict = {
        "meeting_title": meeting_title,
        "meeting_date": meeting_date,
        "duration_minutes": duration_minutes,
        "advisor_name": advisor_name,
        "transcript": [_format_utterance(u) for u in utterances],
    }
    if prior_qa_groups:
        payload["prior_qa_groups"] = [
            {"question": g["question"], "tags": g["tags"]}
            for g in prior_qa_groups
        ]
    return json.dumps(payload, ensure_ascii=False)
