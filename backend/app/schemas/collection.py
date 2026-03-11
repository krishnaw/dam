from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.asset import AssetResponse


class CollectionCreate(BaseModel):
    name: str
    description: str | None = None
    collection_type: str = "collection"
    parent_id: UUID | None = None


class CollectionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class CollectionResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    collection_type: str
    parent_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CollectionWithAssetsResponse(CollectionResponse):
    assets: list[AssetResponse] = []
