# Nate RAG — API (MVC)

Structured FastAPI application. Run from the **repository root** so `backend` is on `PYTHONPATH`.

## Layout

```
backend/app/
  main.py              # App factory + lifespan
  api/v1/              # HTTP routes (View)
  controllers/         # Request orchestration
  schemas/             # Pydantic DTOs
  services/            # Business logic
    rag/               # RAG pipeline (search, LLM, prompts)
  repositories/        # SQLite data access
  models/              # SQLAlchemy ORM
  infrastructure/      # Qdrant, Clerk, DB, OpenAI embeddings
  dependencies/        # FastAPI Depends wiring
  config/              # Settings + logging
```

## Run locally

```bash
# from repo root
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Legacy shim still works:

```bash
uvicorn src.server.main:app --reload
```

## Ingestion CLI

Batch ingestion remains under `src/ingestion/` until migrated to `backend/ingestion/`.
