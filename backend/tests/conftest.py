import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, Text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.database import Base, get_db
from app.services.auth import create_access_token, hash_password

# Compile pgvector Vector type as TEXT for SQLite (no pgvector extension)
from pgvector.sqlalchemy import Vector
from sqlalchemy.ext.compiler import compiles

@compiles(Vector, "sqlite")
def compile_vector_sqlite(type_, compiler, **kw):
    return "TEXT"

# Use SQLite for unit tests (no Docker needed)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        async with session.begin():
            yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    # Avoid importing app at module level to prevent pgvector import errors on SQLite
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Factory fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def make_user():
    def _make(email=None, role="editor", full_name="Test User"):
        from app.models.user import User

        return User(
            id=uuid.uuid4(),
            email=email or f"test-{uuid.uuid4().hex[:8]}@example.com",
            hashed_password=hash_password("testpass123"),
            full_name=full_name,
            role=role,
            is_active=True,
        )

    return _make


@pytest.fixture
def make_asset():
    def _make(**overrides):
        from app.models.asset import Asset, AssetStatus

        defaults = dict(
            id=uuid.uuid4(),
            filename=f"{uuid.uuid4().hex[:8]}.jpg",
            original_filename="test-image.jpg",
            content_type="image/jpeg",
            file_size=1024000,
            width=1920,
            height=1080,
            storage_path=f"assets/{uuid.uuid4().hex}.jpg",
            status=AssetStatus.active,
        )
        defaults.update(overrides)
        return Asset(**defaults)

    return _make


@pytest.fixture
def mock_storage():
    storage = MagicMock()
    storage.upload = MagicMock(return_value="assets/test.jpg")
    storage.download = MagicMock(return_value=b"fake-file-data")
    storage.delete = MagicMock()
    storage.get_url = MagicMock(
        return_value="http://localhost:9000/dam-assets/test.jpg?presigned=true"
    )
    storage.ensure_bucket = MagicMock()
    return storage


@pytest.fixture
def mock_search():
    search = AsyncMock()
    search.index_asset = AsyncMock()
    search.search = AsyncMock(
        return_value={"hits": [], "estimatedTotalHits": 0}
    )
    search.delete_document = AsyncMock()
    return search


@pytest.fixture
def auth_headers():
    """Generate valid auth headers for testing."""
    token = create_access_token(user_id=uuid.uuid4(), role="admin")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def make_auth_headers():
    """Generate auth headers for a specific user id and role."""

    def _make(user_id=None, role="admin"):
        uid = user_id or uuid.uuid4()
        token = create_access_token(user_id=uid, role=role)
        return {"Authorization": f"Bearer {token}"}, uid

    return _make
