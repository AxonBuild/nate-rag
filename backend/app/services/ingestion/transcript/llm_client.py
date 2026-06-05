"""Async LLM client for transcript QA extraction."""
import json
import logging
import re
from dataclasses import dataclass

from openai import AsyncOpenAI

from backend.app.config.settings import settings
from backend.app.services.ingestion.transcript.schemas import TranscriptExtractionResult

logger = logging.getLogger(__name__)

_PRICING: dict[str, tuple[float, float]] = {
    "gpt-5.1": (2.00, 8.00),
    "gpt-4.1": (2.00, 8.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1-nano": (0.10, 0.40),
}


@dataclass
class ExtractionResponse:
    result: TranscriptExtractionResult
    input_tokens: int
    output_tokens: int
    cost: float


def _calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    key = model.split("/")[-1]
    input_price, output_price = _PRICING.get(key, (2.00, 8.00))
    return (input_tokens * input_price + output_tokens * output_price) / 1_000_000


class TranscriptLLMClient:
    def __init__(self) -> None:
        kwargs: dict = {"api_key": settings.openai_api_key}
        if settings.openai_base_url:
            kwargs["base_url"] = settings.openai_base_url
        self._client = AsyncOpenAI(**kwargs)
        self._model = settings.openai_transcript_model or settings.openai_model

    @property
    def model(self) -> str:
        return self._model

    async def extract_qa_groups(
        self,
        system_prompt: str,
        user_message: str,
        model: str | None = None,
    ) -> ExtractionResponse:
        use_model = model or self._model
        response = await self._client.chat.completions.create(
            model=use_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )

        raw = (response.choices[0].message.content or "").strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)
        result = TranscriptExtractionResult.model_validate(data)

        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        cost = _calculate_cost(use_model, input_tokens, output_tokens)

        logger.info(
            "[transcript] llm extract model=%s in=%d out=%d cost=$%.4f groups=%d",
            use_model,
            input_tokens,
            output_tokens,
            cost,
            len(result.qa_groups),
        )
        return ExtractionResponse(
            result=result,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
        )
