from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import assets, collections, metadata, search, sharing, transforms, users, workflows
from app.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup (dev convenience — use alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="DAM API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


app.include_router(assets.router)
app.include_router(search.router)
app.include_router(collections.router)
app.include_router(users.router)
app.include_router(metadata.router)
app.include_router(workflows.asset_router)
app.include_router(workflows.workflow_router)
app.include_router(workflows.notification_router)
app.include_router(transforms.router)
app.include_router(sharing.router)
