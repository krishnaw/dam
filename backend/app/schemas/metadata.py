from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MetadataUpdate(BaseModel):
    key: str
    value: str
    source: str = "manual"


class AssetMetadataResponse(BaseModel):
    id: UUID
    key: str
    value: str
    source: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
