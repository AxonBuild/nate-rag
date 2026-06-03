import json
import os
from dataclasses import dataclass

from openai import OpenAI

from llm_pipeline.schemas import ExtractionResult


@dataclass
class ExtractionResponse:
    result: ExtractionResult
    input_tokens: int
    output_tokens: int
    cost: float


def _make_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1"),
    )


def extract_qa_groups(
    system_prompt: str,
    user_message: str,
    model: str = "openai/gpt-5.1",
) -> ExtractionResponse:
    client = _make_client()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)
    result = ExtractionResult.model_validate(data)

    usage = response.usage
    cost = usage.model_extra.get("cost", 0.0) if usage and usage.model_extra else 0.0
    return ExtractionResponse(
        result=result,
        input_tokens=usage.prompt_tokens if usage else 0,
        output_tokens=usage.completion_tokens if usage else 0,
        cost=cost,
    )
