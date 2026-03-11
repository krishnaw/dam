from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Asset, AssetMetadata
from app.schemas.asset import AssetResponse
from app.schemas.search import SearchResponse
from app.services.auth import get_current_user
from app.services.search import MeilisearchService

router = APIRouter(prefix="/api/search", tags=["search"])


# ---------------------------------------------------------------------------
# Schemas for new endpoints
# ---------------------------------------------------------------------------


class NLPSearchRequest(BaseModel):
    query: str


class SimilarSearchRequest(BaseModel):
    asset_id: UUID | None = None


class ColorSearchRequest(BaseModel):
    color: str  # hex color like "#ff5500"


# ---------------------------------------------------------------------------
# Existing search endpoint
# ---------------------------------------------------------------------------


@router.get("/", response_model=SearchResponse)
async def search_assets(
    q: str = Query(...),
    file_type: str | None = Query(None),
    status: str | None = Query(None),
    min_size: int | None = Query(None),
    max_size: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        svc = MeilisearchService()
        filters = {}
        if file_type:
            filters["content_type"] = file_type
        if status:
            filters["status"] = status
        if min_size is not None:
            filters["file_size_min"] = min_size
        if max_size is not None:
            filters["file_size_max"] = max_size

        results = svc.search(q, filters=filters, page=page, page_size=page_size)
        hit_ids = [hit["id"] for hit in results.get("hits", [])]

        if hit_ids:
            result = await db.execute(select(Asset).where(Asset.id.in_(hit_ids)))
            items = result.scalars().all()
        else:
            items = []

        return SearchResponse(
            items=items,
            total=results.get("estimatedTotalHits", 0),
            query=q,
            facets=results.get("facetDistribution", {}),
        )
    except Exception:
        # Fallback to basic DB search if Meilisearch unavailable
        query = select(Asset).where(
            Asset.original_filename.ilike(f"%{q}%")
            | Asset.description.ilike(f"%{q}%")
        )
        result = await db.execute(query.limit(page_size).offset((page - 1) * page_size))
        items = result.scalars().all()
        return SearchResponse(items=items, total=len(items), query=q, facets={})


# ---------------------------------------------------------------------------
# NLP search
# ---------------------------------------------------------------------------


@router.post("/nlp", response_model=SearchResponse)
async def nlp_search(
    body: NLPSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Parse natural language query via LLM, then search Meilisearch with extracted params."""
    from app.services.ai import parse_nlp_query

    parsed = await parse_nlp_query(body.query)

    keywords = parsed.get("keywords", [])
    search_query = " ".join(keywords) if keywords else body.query

    filters: dict = {}
    file_type = parsed.get("file_type")
    if file_type and file_type != "null":
        filters["content_type"] = file_type

    try:
        svc = MeilisearchService()
        results = svc.search(search_query, filters=filters or None)
        hit_ids = [hit["id"] for hit in results.get("hits", [])]

        if hit_ids:
            result = await db.execute(select(Asset).where(Asset.id.in_(hit_ids)))
            items = result.scalars().all()
        else:
            items = []

        return SearchResponse(
            items=items,
            total=results.get("estimatedTotalHits", 0),
            query=body.query,
            facets=results.get("facetDistribution", {}),
        )
    except Exception:
        # Fallback to DB search using keywords
        if keywords:
            conditions = [
                Asset.original_filename.ilike(f"%{kw}%") | Asset.description.ilike(f"%{kw}%")
                for kw in keywords
            ]
            from sqlalchemy import or_

            query = select(Asset).where(or_(*conditions))
        else:
            query = select(Asset).where(
                Asset.original_filename.ilike(f"%{body.query}%")
                | Asset.description.ilike(f"%{body.query}%")
            )
        result = await db.execute(query.limit(50))
        items = result.scalars().all()
        return SearchResponse(items=items, total=len(items), query=body.query, facets={})


# ---------------------------------------------------------------------------
# Similar (CLIP vector) search
# ---------------------------------------------------------------------------


@router.post("/similar", response_model=list[AssetResponse])
async def find_similar(
    body: SimilarSearchRequest | None = None,
    file: UploadFile | None = File(None),
    asset_id: UUID | None = Query(None),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Find similar assets via CLIP embedding. Provide asset_id or upload an image."""
    query_embedding = None

    # Determine source of embedding
    effective_asset_id = (body.asset_id if body else None) or asset_id
    if effective_asset_id:
        result = await db.execute(select(Asset).where(Asset.id == effective_asset_id))
        asset = result.scalar_one_or_none()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        if asset.embedding is None:
            return []
        query_embedding = asset.embedding
    elif file:
        from app.services.ai import generate_clip_embedding

        image_bytes = await file.read()
        query_embedding = generate_clip_embedding(image_bytes)
    else:
        raise HTTPException(status_code=400, detail="Provide asset_id or upload an image")

    if not query_embedding:
        return []

    # pgvector cosine distance search
    exclude_id = effective_asset_id
    stmt = select(Asset).where(Asset.embedding.isnot(None))
    if exclude_id:
        stmt = stmt.where(Asset.id != exclude_id)
    stmt = stmt.order_by(Asset.embedding.cosine_distance(query_embedding)).limit(limit)

    result = await db.execute(stmt)
    return result.scalars().all()


# ---------------------------------------------------------------------------
# Color search
# ---------------------------------------------------------------------------


@router.post("/color", response_model=list[AssetResponse])
async def search_by_color(
    body: ColorSearchRequest,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Find assets whose dominant color metadata matches the given hex color."""
    color = body.color.lstrip("#").lower()

    # Look for assets with dominant_color metadata matching (exact or close)
    result = await db.execute(
        select(AssetMetadata.asset_id)
        .where(
            AssetMetadata.key == "dominant_color",
            AssetMetadata.value.ilike(f"%{color}%"),
        )
        .limit(limit)
    )
    asset_ids = [row[0] for row in result.all()]

    if not asset_ids:
        return []

    result = await db.execute(select(Asset).where(Asset.id.in_(asset_ids)))
    return result.scalars().all()
