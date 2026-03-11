import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MetadataSource(str, enum.Enum):
    manual = "manual"
    auto = "auto"
    exif = "exif"


class AssetMetadata(Base):
    __tablename__ = "asset_metadata"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE")
    )
    key: Mapped[str] = mapped_column(String(200))
    value: Mapped[str] = mapped_column(Text)
    source: Mapped[MetadataSource] = mapped_column(
        Enum(MetadataSource), default=MetadataSource.manual
    )

    asset: Mapped["Asset"] = relationship(back_populates="metadata_entries")
