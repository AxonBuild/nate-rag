"""Async SQLAlchemy engine and session."""
import logging
from pathlib import Path

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.config.settings import settings
from backend.app.models.orm import Base

logger = logging.getLogger(__name__)

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def _ensure_sqlite_dir() -> None:
    url = settings.database_url
    if url.startswith("sqlite"):
        path_part = url.split("///")[-1]
        if path_part and path_part != ":memory:":
            Path(path_part).parent.mkdir(parents=True, exist_ok=True)


@event.listens_for(engine.sync_engine, "connect")
def _sqlite_pragma(dbapi_conn, _connection_record):
    if settings.database_url.startswith("sqlite"):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


async def init_db() -> None:
    _ensure_sqlite_dir()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database ready: %s", settings.database_url.split("///")[-1])


async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session
