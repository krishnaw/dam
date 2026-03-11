# DAM - Digital Asset Manager

Self-hosted digital asset management system with AI-powered tagging and search.

## Commands

```bash
# Start all services
docker compose up -d

# Run backend tests
docker compose exec dam-api pytest

# Run frontend dev server (standalone)
cd frontend && npm run dev

# Database migrations
docker compose exec dam-api alembic upgrade head

# Create new migration
docker compose exec dam-api alembic revision --autogenerate -m "description"

# View logs
docker compose logs -f dam-api dam-worker
```

## Architecture

| Layer       | Tech                          |
|-------------|-------------------------------|
| API         | FastAPI (async, Python 3.12)  |
| Frontend    | React + Vite + Tailwind + shadcn/ui |
| Database    | PostgreSQL 16 + pgvector      |
| Cache/Queue | Redis 7                       |
| Search      | Meilisearch v1.12             |
| Storage     | MinIO (S3-compatible)         |
| Workers     | Celery                        |
| AI          | LLM fallback chain (Cerebras -> Mistral -> Groq -> Anthropic) |

## Data Flow

1. **Upload**: Client uploads file via API -> stored in MinIO
2. **Processing** (Celery task): Thumbnail generation -> metadata extraction (EXIF, media info) -> AI tagging via LLM -> Meilisearch indexing
3. **Search**: Client queries -> Meilisearch full-text + faceted search, pgvector for similarity
4. **Retrieval**: Presigned MinIO URLs for downloads/previews

## Key Patterns

- **Storage abstraction**: `StorageBackend` protocol - MinIO locally, Azure Blob in production
- **LLM fallback chain**: Try providers in order (Cerebras -> Mistral -> Groq -> Anthropic), fall back on failure
- **Async everywhere**: All DB queries, storage ops, and HTTP calls are async
- **UUID primary keys**: All models use UUID PKs for global uniqueness

## Conventions

- SQLAlchemy 2.0 `mapped_column` style (not legacy `Column`)
- Pydantic v2 schemas with `model_config = ConfigDict(...)`
- Alembic for migrations (autogenerate from models)
- Backend dependency injection via FastAPI `Depends()`
- Frontend state: React Query for server state, zustand for client state

## Testing

See [TEST_COVERAGE.md](TEST_COVERAGE.md) for test statistics.

## Environment

- **Local**: Docker Compose (see `docker-compose.yml`)
- **Production**: Azure (AKS, Blob Storage, Azure Database for PostgreSQL)
- **Config**: All settings via environment variables (`.env` file locally)
