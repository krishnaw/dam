# Test Coverage

Last verified: March 11, 2026

## Summary

| Suite | Tests | Status |
|-------|------:|--------|
| Backend (unit) | 119 | All passing |
| Backend (integration) | 76 | All passing |
| E2E (Playwright) | 83 | All passing |
| **Total** | **278** | **All passing** |

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
