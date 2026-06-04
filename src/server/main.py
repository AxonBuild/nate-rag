"""FastAPI server for nate-rag."""
import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.ingestion.config import settings
from src.ingestion.qdrant_client import QdrantClient
from src.server.dependencies import get_qdrant_client
from src.server.routes import admin, chat, search

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

app = FastAPI(title="Nate RAG Assistant", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(search.router)
app.include_router(admin.router)

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
async def root(request: Request):
    accept = request.headers.get("accept", "")
    if "text/html" in accept and "application/json" not in accept.split(",")[0]:
        index_path = FRONTEND_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path, media_type="text/html")
    return {"message": "Nate RAG API", "docs": "/docs"}


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
