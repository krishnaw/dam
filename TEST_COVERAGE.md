# Test Coverage

Last verified: March 11, 2026

## Summary

| Suite | Tests | Status |
|-------|------:|--------|
| Frontend (unit) | 77 | All passing |
| Backend (unit) | 119 | All passing |
| Backend (integration) | 76 | All passing |
| E2E (Playwright) | 83 | All passing |
| **Total** | **355** | **All passing** |

## Frontend Unit Tests (77)

### Suites

| Test File | Tests |
|-----------|------:|
| Stores (`stores.test.ts`) | 33 |
| AssetCard (`AssetCard.test.tsx`) | 12 |
| SearchBar (`SearchBar.test.tsx`) | 9 |
| API Client (`client.test.ts`) | 8 |
| Utilities (`utils.test.ts`) | 8 |
| AssetGrid (`AssetGrid.test.tsx`) | 7 |

### Methodology

- **Framework**: Vitest + React Testing Library
- **Environment**: jsdom
- **Mocking**: shadcn/ui components mocked as minimal wrappers, react-router-dom mocked
- **Stores**: Tested via `getState()` / `setState()` directly (no React rendering needed)

### How to Run

```bash
cd frontend && npm test

# Watch mode
cd frontend && npm run test:watch

# Single file
cd frontend && npx vitest run src/stores/__tests__/stores.test.ts
```

## Backend Tests (195)

### Unit Tests (119)

- Models (Asset, Metadata, User, Collection, Workflow)
- Schemas (request/response validation)
- Services: Auth, Storage, Search, Media, AI, Video, Document

### Integration Tests (76)

- API contracts: Assets, Collections, Users, Metadata, Workflows, Sharing, Transforms

### Methodology

- **Framework**: pytest-asyncio (auto mode)
- **Database**: SQLite in-memory with aiosqlite (no Docker needed)
- **pgvector compat**: `@compiles(Vector, "sqlite")` returns TEXT
- **Fixtures**: `conftest.py` provides engine, db_session, client, make_user, make_asset

### How to Run

```bash
# All backend tests (inside Docker)
docker compose exec dam-api pytest

# Or locally (no Docker needed — uses SQLite in-memory)
cd backend && pip install -e ".[dev]" && pytest

# Unit tests only
cd backend && pytest tests/unit/

# Integration tests only
cd backend && pytest tests/integration/

# With verbose output and parallel workers
cd backend && pytest -v -n auto
```

## E2E Tests (83)

### Suites

| Spec File | Tests |
|-----------|------:|
| Authentication (`auth.spec.ts`) | 9 |
| Library & Grid (`library.spec.ts`) | 10 |
| Navigation (`navigation.spec.ts`) | 14 |
| Upload (`upload.spec.ts`) | 5 |
| Asset Detail (`asset-detail.spec.ts`) | 7 |
| Search (`search.spec.ts`) | 7 |
| Collections (`collections.spec.ts`) | 6 |
| Comments (`comments.spec.ts`) | 4 |
| Workflows (`workflow-ui.spec.ts`) | 4 |
| Sharing (`sharing-ui.spec.ts`) | 4 |
| AI Search (`ai-search.spec.ts`) | 5 |
| Notifications (`notifications-ui.spec.ts`) | 4 |
| Media Players (`media-players.spec.ts`) | 4 |

### Methodology

- **Framework**: Playwright (headless Chromium)
- **Workers**: 1 (shared database requires serial execution)
- **Mocking**: None -- all tests use real API calls
- **Data setup**: `e2e/helpers/api-helpers.ts` creates test data via backend API in `beforeAll`
- **Cleanup**: Test data removed in `afterAll`
- **Auth**: `loginViaAPI` sets localStorage token then reloads page

### How to Run

```bash
# All E2E tests (requires running services: docker compose up -d)
npx playwright test

# Single spec file
npx playwright test e2e/auth.spec.ts

# With trace on failure
npx playwright test --trace on
```
