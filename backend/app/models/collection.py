import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CollectionType(str, enum.Enum):
    folder = "folder"
    collection = "collection"


class Collection(Base):
    __tablename__ = "collections"

    name: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    collection_type: Mapped[CollectionType] = mapped_column(
        Enum(CollectionType), default=CollectionType.collection
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("collections.id", ondelete="SET NULL"), nullable=True
    )

    children: Mapped[list["Collection"]] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )
    parent: Mapped["Collection | None"] = relationship(
        back_populates="children", remote_side="Collection.id"
    )
    collection_assets: Mapped[list["CollectionAsset"]] = relationship(
        back_populates="collection", cascade="all, delete-orphan"
    )


class CollectionAsset(Base):
    __tablename__ = "collection_assets"
    __table_args__ = (
        UniqueConstraint("collection_id", "asset_id", name="uq_collection_asset"),
    )

    collection_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("collections.id", ondelete="CASCADE")
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE")
    )
    position: Mapped[int] = mapped_column(Integer, default=0)

    collection: Mapped["Collection"] = relationship(
        back_populates="collection_assets"
    )
