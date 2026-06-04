"""LLM client for query refinement and answer generation."""
import json
import logging
import re
from typing import Any

from openai import AsyncOpenAI
from src.ingestion.config import settings
from src.retrieval.prompts.query_refinement import QUERY_REFINEMENT_PROMPT
from src.retrieval.prompts.chat_answer import CHAT_SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)


class LLMClient:

    def __init__(self):
        kwargs = {"api_key": settings.openai_api_key}
        if settings.openai_base_url:
            kwargs["base_url"] = settings.openai_base_url
        self.client = AsyncOpenAI(**kwargs)
        self.model = settings.openai_model
        self.refinement_model = settings.openai_refinement_model or settings.openai_model

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

        response = await self.client.chat.completions.create(
            model=self.refinement_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=400,
        )
        raw = response.choices[0].message.content.strip()

        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning(f"Query refinement JSON parse failed, using original query. Raw: {raw}")
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

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=1500,
        )
        return response.choices[0].message.content.strip()

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
