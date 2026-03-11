import enum
import uuid

from sqlalchemy import BigInteger, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pgvector.sqlalchemy import Vector

from app.database import Base


class AssetStatus(str, enum.Enum):
    draft = "draft"
    processing = "processing"
    active = "active"
    archived = "archived"


class RenditionType(str, enum.Enum):
    original = "original"
    thumbnail = "thumbnail"
    preview = "preview"
    web = "web"


class Asset(Base):
    __tablename__ = "assets"

    filename: Mapped[str] = mapped_column(String(500))
    original_filename: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column(BigInteger)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration: Mapped[float | None] = mapped_column(nullable=True)
    storage_path: Mapped[str] = mapped_column(String(1000))
    status: Mapped[AssetStatus] = mapped_column(
        Enum(AssetStatus), default=AssetStatus.processing
    )
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding = mapped_column(Vector(512), nullable=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    versions: Mapped[list["AssetVersion"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )
    renditions: Mapped[list["Rendition"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )
    metadata_entries: Mapped[list["AssetMetadata"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )


class AssetVersion(Base):
    __tablename__ = "asset_versions"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE")
    )
    version_number: Mapped[int] = mapped_column(Integer)
    storage_path: Mapped[str] = mapped_column(String(1000))
    file_size: Mapped[int] = mapped_column(BigInteger)
    change_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    asset: Mapped["Asset"] = relationship(back_populates="versions")


class Rendition(Base):
    __tablename__ = "renditions"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE")
    )
    rendition_type: Mapped[RenditionType] = mapped_column(Enum(RenditionType))
    storage_path: Mapped[str] = mapped_column(String(1000))
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_format: Mapped[str | None] = mapped_column(String(20), nullable=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    asset: Mapped["Asset"] = relationship(back_populates="renditions")
