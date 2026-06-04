"""LLM client for query refinement and answer generation."""
import json
import logging
import re
import time
from typing import Any

from openai import AsyncOpenAI
from src.ingestion.config import settings
from src.retrieval.prompts.query_refinement import QUERY_REFINEMENT_PROMPT
from src.retrieval.prompts.answer_verification import ANSWER_VERIFICATION_PROMPT
from src.retrieval.prompts.chat_answer import CHAT_SYSTEM_PROMPT, build_user_prompt
from src.retrieval import chat_logging as chat_log

logger = logging.getLogger(__name__)


def _log_llm_usage(step: str, model: str, response: Any, elapsed_ms: float) -> None:
    usage = getattr(response, "usage", None)
    if usage:
        chat_log.logger.info(
            "[chat] llm step=%s model=%s elapsed_ms=%.0f prompt_tokens=%s "
            "completion_tokens=%s total_tokens=%s",
            step,
            model,
            elapsed_ms,
            getattr(usage, "prompt_tokens", "?"),
            getattr(usage, "completion_tokens", "?"),
            getattr(usage, "total_tokens", "?"),
        )
    else:
        chat_log.logger.info(
            "[chat] llm step=%s model=%s elapsed_ms=%.0f",
            step,
            model,
            elapsed_ms,
        )


class LLMClient:

    def __init__(self):
        kwargs = {"api_key": settings.openai_api_key}
        if settings.openai_base_url:
            kwargs["base_url"] = settings.openai_base_url
        self.client = AsyncOpenAI(**kwargs)
        self.model = settings.openai_model
        self.refinement_model = settings.openai_refinement_model or settings.openai_model
        self.verification_model = (
            settings.openai_verification_model
            or settings.openai_refinement_model
            or settings.openai_model
        )

    async def refine_query(
        self,
        query: str,
        chat_history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Refine query and extract keywords for hybrid search."""
        if chat_history:
            lines = [f"{m['role'].capitalize()}: {m['content']}" for m in chat_history[-6:]]
            history_context = "\n".join(lines)
        else:
            history_context = "No prior conversation."

        prompt = QUERY_REFINEMENT_PROMPT.format(
            query=query,
            chat_history_context=history_context,
        )
        chat_log.logger.info(
            "[chat] llm step=refine start model=%s prompt_chars=%d history_msgs=%d",
            self.refinement_model,
            len(prompt),
            len(chat_history or []),
        )

        t0 = time.time()
        response = await self.client.chat.completions.create(
            model=self.refinement_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=400,
        )
        _log_llm_usage("refine", self.refinement_model, response, (time.time() - t0) * 1000)
        raw = response.choices[0].message.content.strip()

        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            chat_log.logger.warning(
                "[chat] refine json parse failed, using original query. raw=%r",
                raw[:300],
            )
            result = {
                "refined_query": query,
                "keywords": [],
                "number_of_chunks": 10,
                "full_page_content": False,
            }

        return {
            "refined_query": result.get("refined_query", query),
            "keywords": result.get("keywords", []),
            "number_of_chunks": result.get("number_of_chunks", 10),
            "full_page_content": result.get("full_page_content", False),
        }

    async def generate_answer(
        self,
        question: str,
        context_text: str,
        chat_history: list[dict[str, Any]] | None = None,
        system_prompt_override: str | None = None,
    ) -> str:
        """Generate a final answer given context and question."""
        system = system_prompt_override.strip() if system_prompt_override else CHAT_SYSTEM_PROMPT
        user_prompt = build_user_prompt(context_text=context_text, question=question)

        messages = [{"role": "system", "content": system}]
        for msg in (chat_history or [])[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_prompt})
        chat_log.logger.info(
            "[chat] llm step=generate start model=%s context_chars=%d history_msgs=%d "
            "custom_system=%s",
            self.model,
            len(context_text),
            len(chat_history or []),
            bool(system_prompt_override and system_prompt_override.strip()),
        )

        t0 = time.time()
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=1500,
        )
        elapsed_ms = (time.time() - t0) * 1000
        _log_llm_usage("generate", self.model, response, elapsed_ms)
        answer = response.choices[0].message.content.strip()
        chat_log.logger.info("[chat] generate draft_chars=%d", len(answer))
        return answer

    async def generate_answer_stream(
        self,
        question: str,
        context_text: str,
        chat_history: list[dict[str, Any]] | None = None,
        system_prompt_override: str | None = None,
    ):
        """Yield answer text chunks as they arrive from the LLM."""
        system = system_prompt_override.strip() if system_prompt_override else CHAT_SYSTEM_PROMPT
        user_prompt = build_user_prompt(context_text=context_text, question=question)

        messages = [{"role": "system", "content": system}]
        for msg in (chat_history or [])[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_prompt})

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=1500,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta

    async def verify_answer(
        self,
        question: str,
        context_text: str,
        draft_answer: str,
    ) -> tuple[dict[str, Any], int]:
        """
        Single-shot verification: is_correct, reasoning; corrected_answer only if wrong.
        Returns (verdict, api_attempts).
        """
        prompt = ANSWER_VERIFICATION_PROMPT.format(
            context_text=context_text,
            question=question,
            draft_answer=draft_answer,
        )
        prompt_chars = len(prompt)
        draft_chars = len(draft_answer)
        chat_log.logger.info(
            "[chat] llm step=verify start model=%s prompt_chars=%d draft_chars=%d",
            self.verification_model,
            prompt_chars,
            draft_chars,
        )
        kwargs: dict[str, Any] = {
            "model": self.verification_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 2000,
            "response_format": {"type": "json_object"},
        }

        t0 = time.time()
        response = await self.client.chat.completions.create(**kwargs)
        elapsed_ms = (time.time() - t0) * 1000
        raw = response.choices[0].message.content.strip()

        _log_llm_usage("verify", self.verification_model, response, elapsed_ms)

        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            chat_log.logger.warning(
                "[chat] verify json parse failed elapsed_ms=%.0f prompt_chars=%d raw=%r",
                elapsed_ms,
                prompt_chars,
                raw[:500],
            )
            return {
                "is_correct": True,
                "reasoning": "Verification parse failed; draft kept.",
                "corrected_answer": None,
            }, 1

        is_correct = bool(result.get("is_correct", False))
        reasoning = str(result.get("reasoning", "")).strip()
        corrected_raw = result.get("corrected_answer")
        corrected = (
            str(corrected_raw).strip()
            if corrected_raw is not None and not is_correct
            else None
        )

        if not is_correct and not corrected:
            chat_log.logger.warning(
                "[chat] verify denied draft but no corrected_answer; keeping draft"
            )
            is_correct = True
            reasoning = (reasoning + " (No correction provided; draft kept.)").strip()

        corrected_chars = len(corrected) if corrected else 0
        chat_log.log_verification(
            elapsed_ms=elapsed_ms,
            model=self.verification_model,
            is_correct=is_correct,
            prompt_chars=prompt_chars,
            draft_chars=draft_chars,
            corrected_chars=corrected_chars,
            reasoning_preview=reasoning,
        )

        verdict: dict[str, Any] = {
            "is_correct": is_correct,
            "reasoning": reasoning,
            "corrected_answer": corrected,
        }
        return verdict, 1
