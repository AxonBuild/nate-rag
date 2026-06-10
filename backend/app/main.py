"""FastAPI application entrypoint."""
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.v1.router import api_router
from backend.app.config.logging_config import setup_logging
from backend.app.dependencies.container import get_qdrant_client
from backend.app.infrastructure.database.session import init_db

setup_logging()
logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"

QDRANT_HEARTBEAT_INTERVAL = 3600


async def _qdrant_heartbeat() -> None:
    client = get_qdrant_client()
    while True:
        await asyncio.sleep(QDRANT_HEARTBEAT_INTERVAL)
        try:
            await asyncio.to_thread(client.client.get_collections)
            logger.info("Qdrant heartbeat OK")
        except Exception as e:
            logger.warning(f"Qdrant heartbeat failed: {e}")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    heartbeat_task = asyncio.create_task(_qdrant_heartbeat())
    yield
    heartbeat_task.cancel()


def create_app() -> FastAPI:
    application = FastAPI(title="Nate's AI API", version="1.0.0", lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_router)

    if STATIC_DIR.is_dir():
        application.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

        @application.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            file = STATIC_DIR / full_path
            if file.is_file():
                return FileResponse(file)
            return FileResponse(STATIC_DIR / "index.html")

    return application


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
