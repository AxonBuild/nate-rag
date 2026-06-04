"""Structured logs for the chat / RAG pipeline."""
import logging
from typing import Any, Optional

logger = logging.getLogger("nate.chat")


def _preview(text: str, max_len: int = 120) -> str:
    t = " ".join((text or "").split())
    if len(t) <= max_len:
        return t
    return t[: max_len - 1] + "…"


def log_request(
    *,
    mode: str,
    question: str,
    history_len: int = 0,
    retrieval_limit: Optional[int] = None,
    topic: Optional[str] = None,
    doc_type: Optional[str] = None,
    has_system_override: bool = False,
) -> None:
    logger.info(
        "[chat] request mode=%s history=%d retrieval_limit=%s topic=%s doc_type=%s "
        "system_override=%s question=%r",
        mode,
        history_len,
        retrieval_limit if retrieval_limit is not None else "auto",
        topic or "-",
        doc_type or "-",
        has_system_override,
        _preview(question, 200),
    )


def log_phase(phase: str, elapsed_ms: float, **extra: Any) -> None:
    parts = [f"[chat] phase={phase} elapsed_ms={elapsed_ms:.0f}"]
    for key, val in extra.items():
        if val is None:
            continue
        if isinstance(val, float):
            parts.append(f"{key}={val:.4f}" if "score" in key else f"{key}={val}")
        elif isinstance(val, (list, tuple)):
            parts.append(f"{key}={list(val)!r}")
        else:
            parts.append(f"{key}={val!r}")
    logger.info(" ".join(parts))


def log_refinement(refinement: dict[str, Any], n_chunks: int, elapsed_ms: float) -> None:
    logger.info(
        "[chat] refinement done elapsed_ms=%.0f n_chunks=%d keywords=%d refined_query=%r",
        elapsed_ms,
        n_chunks,
        len(refinement.get("keywords") or []),
        _preview(refinement.get("refined_query", ""), 160),
    )


def log_retrieval(
    *,
    elapsed_ms: float,
    n_chunks: int,
    kb_count: int,
    qa_count: int,
    context_chars: int,
    top_score: Optional[float] = None,
) -> None:
    logger.info(
        "[chat] retrieval done elapsed_ms=%.0f chunks=%d kb=%d qa=%d context_chars=%d top_score=%s",
        elapsed_ms,
        n_chunks,
        kb_count,
        qa_count,
        context_chars,
        f"{top_score:.4f}" if top_score is not None else "-",
    )


def log_generation(
    *,
    elapsed_ms: float,
    model: str,
    draft_chars: int,
    context_chars: int,
    history_len: int,
) -> None:
    logger.info(
        "[chat] generation done model=%s elapsed_ms=%.0f draft_chars=%d context_chars=%d history=%d",
        model,
        elapsed_ms,
        draft_chars,
        context_chars,
        history_len,
    )


def log_verification(
    *,
    elapsed_ms: float,
    model: str,
    is_correct: bool,
    prompt_chars: int,
    draft_chars: int,
    corrected_chars: int,
    reasoning_preview: str,
) -> None:
    outcome = "succeeded" if is_correct else "denied"
    logger.info(
        "[chat] verification done model=%s elapsed_ms=%.0f outcome=%s "
        "prompt_chars=%d draft_chars=%d corrected_chars=%d reasoning=%r",
        model,
        elapsed_ms,
        outcome,
        prompt_chars,
        draft_chars,
        corrected_chars,
        _preview(reasoning_preview, 200),
    )


def log_complete(
    *,
    mode: str,
    timing: dict[str, float],
    verification: Optional[dict[str, Any]],
    answer_chars: int,
    source_count: int,
) -> None:
    v = verification or {}
    logger.info(
        "[chat] complete mode=%s total_ms=%.0f refine_ms=%.0f embed_ms=%.0f "
        "retrieve_ms=%.0f generate_ms=%.0f verify_ms=%.0f verified=%s corrected=%s "
        "answer_chars=%d sources=%d",
        mode,
        timing.get("total_chat_ms") or timing.get("total_ms") or 0,
        timing.get("query_refinement_ms", 0),
        timing.get("embedding_ms", 0),
        timing.get("retrieval_ms", 0),
        timing.get("answer_generation_ms", 0),
        timing.get("verification_ms", 0),
        v.get("is_correct") if verification else "-",
        v.get("was_corrected") if verification else "-",
        answer_chars,
        source_count,
    )
