# DAM - Digital Asset Manager

A self-hosted digital asset management platform with AI-powered tagging, multi-modal search (keyword, NLP, visual similarity, color), real-time collaboration, and enterprise media processing.

## Architecture

```
                     ┌──────────────────┐
                     │   dam-web :3001  │
                     │  React 19 / Vite │
                     └────────┬─────────┘
                              │
                     ┌────────┴─────────┐
                     │  dam-api :8000   │
                     │  FastAPI (async) │
                     └──┬──┬──┬──┬──┬──┘
                        │  │  │  │  │
          ┌─────────────┘  │  │  │  └─────────────┐
          │                │  │  │                 │
   ┌──────┴──────┐  ┌─────┴──┴──┴──┐   ┌─────────┴───┐
   │  dam-db     │  │  dam-redis   │   │ dam-search  │
   │ PG+pgvector │  │   Redis 7    │   │ Meilisearch │
   │  :5432      │  │   :6379      │   │   :7700     │
   └─────────────┘  └──────┬───────┘   └─────────────┘
                           │
                    ┌──────┴──────┐
                    │ dam-worker  │
                    │   Celery    │
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │ dam-storage │
                    │    MinIO    │
                    │ :9000/:9001 │
                    └─────────────┘
```

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| API | FastAPI (Python 3.12, async) | REST API with OpenAPI docs |
| Frontend | React 19 + Vite 7 + TailwindCSS 4 + shadcn/ui | Single-page application |
| Database | PostgreSQL 16 + pgvector | Relational data + vector similarity |
| Cache & Broker | Redis 7 | Caching + Celery task broker |
| Search | Meilisearch v1.12 | Full-text + faceted search |
| Object Storage | MinIO | S3-compatible file storage |
| Task Queue | Celery | Async processing pipeline |
| AI/ML | LLM fallback chain + CLIP + OCR | Auto-tagging, embeddings, text extraction |

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2+
- [Node.js](https://nodejs.org/) 18+ and npm (for frontend dev and E2E tests)
- [Python](https://www.python.org/) 3.11+ (for running backend tests locally)
- Git

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/krishnaw/dam.git
cd dam

# 2. Set up environment
cp .env.example .env
# Edit .env with your API keys (optional — AI tagging won't work without them)

# 3. Start all services
docker compose up -d

# 4. Run database migrations
docker compose exec dam-api alembic upgrade head

# 5. Open the app
#    Frontend:       http://localhost:3001
#    API docs:       http://localhost:8000/docs
#    MinIO console:  http://localhost:9001  (user: dam_dev_user / pass: dam_dev_password)
#    Meilisearch:    http://localhost:7700
```

## Development

### Backend (inside Docker)

```bash
# View API logs
docker compose logs -f dam-api

# View worker logs
docker compose logs -f dam-worker

# Restart the API after code changes (auto-reload is enabled)
docker compose restart dam-api

# Rebuild after dependency changes (pyproject.toml)
docker compose up -d --build dam-api dam-worker

# Run a one-off command inside the API container
docker compose exec dam-api python -c "from app.config import settings; print(settings.database_url)"
```

### Backend (local, without Docker)

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# Install dependencies
pip install -e ".[dev]"

# Run tests (uses SQLite in-memory, no Docker needed)
pytest

# Run tests with parallel workers
pytest -n auto
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (proxies API to http://localhost:8000)
npm run dev
# Opens at http://localhost:5173

# Build for production
npm run build

# Lint
npm run lint
```

### Database Migrations

```bash
# Apply all pending migrations
docker compose exec dam-api alembic upgrade head

# Create a new migration after model changes
docker compose exec dam-api alembic revision --autogenerate -m "describe your change"

# Downgrade one revision
docker compose exec dam-api alembic downgrade -1

# View migration history
docker compose exec dam-api alembic history
```

## Testing

See [TEST_COVERAGE.md](TEST_COVERAGE.md) for detailed test statistics and suite breakdowns.

### Backend Tests (pytest)

```bash
# Inside Docker
docker compose exec dam-api pytest

# Or locally (no Docker needed — uses SQLite in-memory)
cd backend
pip install -e ".[dev]"
pytest

# Run with verbose output
pytest -v --tb=long

# Run a specific test file
pytest tests/unit/test_auth.py

# Run a specific test
pytest tests/unit/test_auth.py::TestPasswordHashing::test_verify_correct_password

# Run with parallel workers (faster)
pytest -n auto
```

### E2E Tests (Playwright)

E2E tests use **real API calls** against running Docker services. No HTTP mocking.

```bash
# 1. Ensure Docker services are running
docker compose up -d

# 2. Run database migrations
docker compose exec dam-api alembic upgrade head

# 3. Install Playwright (from project root)
npm install
npx playwright install chromium

# 4. Run all E2E tests
npx playwright test

# 5. Run a specific test file
npx playwright test e2e/auth.spec.ts

# 6. Run with visible browser (debugging)
npx playwright test --headed

# 7. View test report
npx playwright show-report
```

**Important**: E2E tests run with `workers: 1` because all tests share a single database. Each test file sets up and tears down its own data.

### Generate Showcase PDF

```bash
# Generate test images (required for screenshot tests)
python e2e/helpers/generate-test-images.py

# Run screenshot capture tests
npx playwright test e2e/screenshots.spec.ts

# Generate the PDF
pip install PyMuPDF Pillow
python generate_pdf.py
# Output: DAM_Showcase.pdf
```

## Project Structure

```
dam/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Pydantic Settings (from env vars)
│   │   ├── database.py          # Async SQLAlchemy engine & session
│   │   ├── models/              # SQLAlchemy 2.0 models (5 files)
│   │   ├── schemas/             # Pydantic v2 request/response schemas
│   │   ├── api/                 # Route handlers (8 modules)
│   │   ├── services/            # Business logic (storage, auth, media, AI, search, etc.)
│   │   └── tasks/               # Celery tasks (ingest, AI tag, transcode)
│   ├── alembic/                 # Database migrations
│   ├── tests/
│   │   ├── unit/                # Unit tests (119)
│   │   ├── integration/         # Integration tests (76)
│   │   └── conftest.py          # Fixtures (engine, session, client, factories)
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/                 # TanStack Query hooks (10 modules)
│   │   ├── components/          # React components (asset grid, media players, etc.)
│   │   ├── pages/               # Route pages (10)
│   │   ├── stores/              # Zustand stores (auth, assets, search, etc.)
│   │   └── types/               # TypeScript type definitions
│   ├── package.json
│   └── Dockerfile
├── e2e/                         # Playwright E2E tests (13 spec files)
│   └── helpers/                 # Test utilities and image generators
├── docker-compose.yml           # 7 services (API, Web, Worker, DB, Redis, Search, Storage)
├── playwright.config.ts         # Playwright config (headless chromium, workers: 1)
├── .env.example                 # Environment variable template
├── CLAUDE.md                    # Claude Code project instructions
├── TEST_COVERAGE.md             # Test statistics and suite details
└── generate_pdf.py              # PDF showcase generator
```

## API Documentation

When the API is running, interactive documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register` | Register a new user |
| `POST` | `/api/auth/login` | Login (returns JWT) |
| `GET` | `/api/assets` | List assets (paginated) |
| `POST` | `/api/assets/upload` | Upload a file |
| `GET` | `/api/assets/{id}` | Get asset details |
| `GET` | `/api/assets/{id}/thumbnail` | Get asset thumbnail |
| `GET` | `/api/assets/{id}/transform` | On-the-fly image transform |
| `POST` | `/api/assets/{id}/transcode` | Queue video transcode |
| `GET` | `/api/assets/{id}/preview` | Document page preview |
| `GET` | `/api/search` | Full-text search |
| `GET/POST` | `/api/collections/*` | Collection CRUD |
| `POST` | `/api/assets/{id}/share` | Create share link |
| `GET/POST` | `/api/assets/{id}/comments` | Comments CRUD |
| `POST` | `/api/assets/{id}/workflow/*` | Workflow actions |

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `MINIO_ENDPOINT` | Yes | MinIO host:port |
| `MINIO_ACCESS_KEY` | Yes | MinIO access key |
| `MINIO_SECRET_KEY` | Yes | MinIO secret key |
| `MEILISEARCH_URL` | Yes | Meilisearch URL |
| `MEILISEARCH_KEY` | Yes | Meilisearch master key |
| `JWT_SECRET` | Yes | JWT signing secret |
| `CEREBRAS_API_KEY` | No | Cerebras LLM key (free tier) |
| `MISTRAL_API_KEY` | No | Mistral LLM key (free tier) |
| `GROQ_API_KEY` | No | Groq LLM key (free tier) |
| `ANTHROPIC_API_KEY` | No | Anthropic key (paid, last resort) |
| `GOOGLE_CLIENT_ID` | No | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | No | Google OAuth client secret |

## Azure Migration Path

The application swaps infrastructure backends without code changes:

| Local (Docker) | Azure |
|----------------|-------|
| MinIO | Azure Blob Storage |
| PostgreSQL | Azure Database for PostgreSQL |
| Redis | Azure Cache for Redis |
| Meilisearch | Azure AI Search |
| Docker Compose | Azure Kubernetes Service (AKS) |

Storage uses a `StorageBackend` protocol abstraction — switching from MinIO to Azure Blob requires only a config change and the Azure backend implementation.

## Stopping & Resetting

```bash
# Stop all services (preserves data)
docker compose down

# Stop and remove all data (full reset)
docker compose down -v

# Remove built images too
docker compose down -v --rmi local
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `port 8000 already in use` | Stop other services on 8000 or change port in `docker-compose.yml` |
| `alembic upgrade` fails | Ensure dam-db is healthy: `docker compose ps` |
| Frontend can't reach API | Check dam-api is running: `docker compose logs dam-api` |
| Thumbnails not generating | Check dam-worker is running: `docker compose logs dam-worker` |
| AI tagging not working | Set LLM API keys in `.env` (at least one of Cerebras/Mistral/Groq) |
| MinIO connection refused | Wait 10s after `docker compose up` for MinIO to initialize |
| E2E tests fail on first run | Run `docker compose exec dam-api alembic upgrade head` first |
| Playwright not installed | Run `npx playwright install chromium` from project root |
