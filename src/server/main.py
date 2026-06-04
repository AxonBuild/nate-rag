"""FastAPI server for nate-rag."""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from src.db.database import init_db
from src.ingestion.config import settings
from src.ingestion.qdrant_client import QdrantClient
from src.server.dependencies import get_qdrant_client
from src.server.routes import admin, chat, conversations, search

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logging.getLogger("nate.chat").setLevel(logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Nate's AI API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(search.router)
app.include_router(admin.router)


@app.get("/")
async def root():
    return {"message": "Nate's AI API", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/config")
async def config():
    return {
        "qdrant_collection_name": settings.qdrant_collection_name,
        "openai_embedding_model": settings.openai_embedding_model,
        "openai_model": settings.openai_model,
    }


@app.get("/stats")
async def stats(qdrant: QdrantClient = Depends(get_qdrant_client)):
    try:
        info = await asyncio.to_thread(qdrant.client.get_collection, qdrant.collection_name)

        # Count by file_type using scroll
        counts: dict[str, int] = {}
        offset = None
        while True:
            result, offset = qdrant.client.scroll(
                collection_name=qdrant.collection_name,
                limit=250,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for p in result:
                ft = (p.payload or {}).get("file_type") or "normal"
                counts[ft] = counts.get(ft, 0) + 1
            if offset is None:
                break

        return {
            "status": "Active",
            "points_count": info.points_count,
            "kb_chunks": counts.get("normal", 0),
            "qa_pairs": counts.get("qa_pair", 0),
            "vectors_config": "Named Vectors (content + sparse)",
        }
    except Exception as e:
        logger.warning(f"Stats failed: {e}")
        return {"status": "error", "points_count": 0}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.server.main:app", host="0.0.0.0", port=8000, reload=True)
