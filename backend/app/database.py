import uuid
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


def _utcnow() -> datetime:
    """Return a timezone-naive UTC datetime for TIMESTAMP WITHOUT TIME ZONE columns."""
    return datetime.utcnow()


class Base(DeclarativeBase):
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        default=_utcnow,
        onupdate=_utcnow,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
