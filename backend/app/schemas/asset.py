from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field


class AssetCreate(BaseModel):
    description: str | None = None


class AssetUpdate(BaseModel):
    description: str | None = None
    status: str | None = None


class AssetResponse(BaseModel):
    id: UUID
    filename: str
    original_filename: str
    content_type: str = Field(alias="content_type", serialization_alias="mime_type")
    file_size: int
    width: int | None = None
    height: int | None = None
    duration: float | None = None
    storage_path: str = ""
    status: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = Field(default=None, serialization_alias="uploaded_by")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def thumbnail_path(self) -> str | None:
        if self.content_type and self.content_type.startswith("image/"):
            return f"/api/assets/{self.id}/thumbnail"
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def tags(self) -> list:
        return []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def metadata(self) -> dict:
        return {}

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AssetListResponse(BaseModel):
    items: list[AssetResponse]
    total: int
    page: int
    page_size: int = Field(serialization_alias="per_page")

    model_config = ConfigDict(populate_by_name=True)


class AssetVersionResponse(BaseModel):
    id: UUID
    version_number: int
    file_size: int
    change_notes: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RenditionResponse(BaseModel):
    id: UUID
    rendition_type: str
    width: int | None = None
    height: int | None = None
    file_format: str | None = None
    file_size: int | None = None

    model_config = ConfigDict(from_attributes=True)
