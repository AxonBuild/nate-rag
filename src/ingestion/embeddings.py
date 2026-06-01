"""OpenAI embedding generation."""
from typing import List
from openai import AsyncOpenAI
from src.ingestion.config import settings


class EmbeddingService:

    def __init__(self):
        kwargs = {"api_key": settings.openai_api_key}
        if settings.openai_base_url:
            kwargs["base_url"] = settings.openai_base_url
        self.client = AsyncOpenAI(**kwargs)
        self.model = settings.openai_embedding_model

    async def generate_embedding(self, text: str) -> List[float]:
        response = await self.client.embeddings.create(model=self.model, input=text)
        return response.data[0].embedding

    async def generate_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = await self.client.embeddings.create(model=self.model, input=batch)
            results.extend(item.embedding for item in response.data)
        return results
