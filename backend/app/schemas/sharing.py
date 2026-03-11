from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ShareCreate(BaseModel):
    asset_id: UUID | None = None
    collection_id: UUID | None = None
    expires_at: datetime | None = None
    password: str | None = None
    permissions: str = "view"


class ShareResponse(BaseModel):
    id: UUID
    token: str
    asset_id: UUID | None = None
    collection_id: UUID | None = None
    expires_at: datetime | None = None
    permissions: str
    is_active: bool
    access_count: int
    created_at: datetime
    share_url: str

    model_config = ConfigDict(from_attributes=True)


class ShareUpdate(BaseModel):
    expires_at: datetime | None = None
    password: str | None = None
    permissions: str | None = None
    is_active: bool | None = None


class ShareAccess(BaseModel):
    password: str | None = None
