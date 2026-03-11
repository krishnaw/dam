from datetime import date

from pydantic import BaseModel

from app.schemas.asset import AssetResponse


class SearchQuery(BaseModel):
    q: str
    file_type: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    min_size: int | None = None
    max_size: int | None = None
    status: str | None = None
    page: int = 1
    page_size: int = 50


class SearchResponse(BaseModel):
    items: list[AssetResponse]
    total: int
    query: str
    facets: dict = {}
