"""Fireflies transcript.json → ProcessedTranscript (QA extraction)."""
import logging
import re
from typing import Any

from backend.app.services.ingestion.transcript.llm_client import TranscriptLLMClient
from backend.app.services.ingestion.transcript.schemas import (
    ProcessedTranscript,
    TranscriptExtractionResult,
    TranscriptQAGroupFull,
)
from backend.app.services.ingestion.transcript.utterances import (
    build_user_message,
    chunk_utterances,
    detect_advisor,
    estimate_duration_minutes,
    get_system_prompt,
    load_utterances,
)

logger = logging.getLogger(__name__)


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "transcript"


def _reconstruct(result: TranscriptExtractionResult) -> list[TranscriptQAGroupFull]:
    groups: list[TranscriptQAGroupFull] = []
    for g in result.qa_groups:
        if not g.advisor_utterance_indices or not g.answer.strip():
            continue
        groups.append(
            TranscriptQAGroupFull(
                question=g.question,
                tags=g.tags,
                reasoning=g.reasoning,
                answer=g.answer,
                confidence=g.confidence,
                advisor_utterance_indices=g.advisor_utterance_indices,
            )
        )
    return groups


def _deduplicate(groups: list[TranscriptQAGroupFull]) -> list[TranscriptQAGroupFull]:
    seen: set[str] = set()
    unique: list[TranscriptQAGroupFull] = []
    for g in groups:
        key = g.question.strip().lower()
        if key not in seen:
            unique.append(g)
            seen.add(key)
    return unique


class TranscriptProcessor:
    def __init__(self, llm: TranscriptLLMClient | None = None) -> None:
        self._llm = llm or TranscriptLLMClient()

    async def process_transcript_json(
        self,
        transcript_json: dict[str, Any],
        *,
        client_name: str = "Unknown client",
        meeting_title: str | None = None,
        meeting_date: str | None = None,
        duration_minutes: int | None = None,
        source_folder: str | None = None,
        attendees: list[str] | None = None,
        model: str | None = None,
    ) -> tuple[ProcessedTranscript, float, dict[str, int]]:
        """
        Extract QA pairs from a Fireflies-style transcript.json payload.

        Returns (processed_transcript, total_cost_usd, token_usage).
        """
        utterances = load_utterances(transcript_json)
        if not utterances:
            raise ValueError("Transcript JSON has no utterances in `data`")

        advisor_name = detect_advisor(utterances)
        chunks = chunk_utterances(utterances)
        resolved_title = meeting_title or "Meeting transcript"
        resolved_date = meeting_date or ""
        resolved_duration = (
            duration_minutes
            if duration_minutes is not None
            else estimate_duration_minutes(utterances)
        )
        resolved_folder = source_folder or _slugify(resolved_title)
        resolved_attendees = attendees or []

        logger.info(
            "[transcript] processing client=%r utterances=%d chunks=%d advisor=%r",
            client_name,
            len(utterances),
            len(chunks),
            advisor_name,
        )

        system_prompt = get_system_prompt()
        all_groups: list[TranscriptQAGroupFull] = []
        used_indices: set[int] = set()
        total_input_tokens = 0
        total_output_tokens = 0
        total_cost = 0.0

        for i, chunk in enumerate(chunks, 1):
            prior = [
                {"question": g.question, "tags": g.tags}
                for g in all_groups[-3:]
            ] or None

            user_msg = build_user_message(
                meeting_title=resolved_title,
                meeting_date=resolved_date,
                duration_minutes=resolved_duration,
                utterances=chunk,
                advisor_name=advisor_name,
                prior_qa_groups=prior,
            )

            response = await self._llm.extract_qa_groups(
                system_prompt=system_prompt,
                user_message=user_msg,
                model=model,
            )

            groups = _reconstruct(response.result)
            all_groups.extend(groups)
            for g in response.result.qa_groups:
                used_indices.update(g.advisor_utterance_indices)
                used_indices.update(g.client_utterance_indices)

            total_input_tokens += response.input_tokens
            total_output_tokens += response.output_tokens
            total_cost += response.cost

            logger.info(
                "[transcript] chunk %d/%d utterances %d–%d → %d groups ($%.4f)",
                i,
                len(chunks),
                chunk[0]["index"],
                chunk[-1]["index"],
                len(groups),
                response.cost,
            )

        all_groups = _deduplicate(all_groups)
        utterance_indices = {u["index"] for u in utterances}
        skipped_count = len(utterances) - len(used_indices & utterance_indices)

        result = ProcessedTranscript(
            client=client_name,
            meeting_title=resolved_title,
            meeting_date=resolved_date,
            duration_minutes=resolved_duration,
            source_folder=resolved_folder,
            attendees=resolved_attendees,
            speakers=sorted({u["speaker_name"] for u in utterances}),
            total_utterances=len(utterances),
            skipped_utterances=skipped_count,
            qa_groups=all_groups,
        )

        logger.info(
            "[transcript] done client=%r qa_groups=%d cost=$%.4f tokens=%d/%d",
            client_name,
            len(all_groups),
            total_cost,
            total_input_tokens,
            total_output_tokens,
        )

        return result, total_cost, {
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "chunks": len(chunks),
        }
