"""LLM client — summary generation for Level 0 chunks."""
from openai import AsyncOpenAI
from src.ingestion.config import settings

SUMMARY_PROMPT = """Create a concise summary of the following tax/financial content in under {max_length} words.
Focus on the key rules, thresholds, strategies, and concepts. Be factual and precise.

Content:
{text}

Summary:"""


class LLMClient:

    def __init__(self):
        kwargs = {"api_key": settings.openai_api_key}
        if settings.openai_base_url:
            kwargs["base_url"] = settings.openai_base_url
        self.client = AsyncOpenAI(**kwargs)
        self.model = settings.openai_model

    async def generate_summary(self, text: str, max_length: int = 200) -> str:
        prompt = SUMMARY_PROMPT.format(max_length=max_length, text=text)
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a tax expert assistant that creates concise, accurate summaries."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=min(max_length * 2, 500),
        )
        return response.choices[0].message.content.strip()
