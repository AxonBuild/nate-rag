import json
import os

from openai import OpenAI

from llm_pipeline.schemas import ExtractionResult


def _make_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1"),
    )


def extract_qa_groups(
    system_prompt: str,
    user_message: str,
    model: str = "openai/gpt-4o-mini",
) -> ExtractionResult:
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
    return ExtractionResult.model_validate(data)
