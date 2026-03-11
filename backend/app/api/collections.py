from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Asset, Collection, CollectionAsset
from app.schemas.asset import AssetResponse
from app.schemas.collection import (
    CollectionCreate,
    CollectionResponse,
    CollectionUpdate,
    CollectionWithAssetsResponse,
)
from app.services.auth import get_current_user, require_editor, require_manager, require_viewer

router = APIRouter(prefix="/api/collections", tags=["collections"])


@router.post("/", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    body: CollectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    collection = Collection(
        name=body.name,
        description=body.description,
        collection_type=body.collection_type,
        parent_id=body.parent_id,
    )
    db.add(collection)
    await db.flush()
    await db.refresh(collection)
    return collection


@router.get("/", response_model=list[CollectionResponse])
async def list_collections(
    parent_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_viewer),
):
    query = select(Collection)
    if parent_id is not None:
        query = query.where(Collection.parent_id == parent_id)
    else:
        query = query.where(Collection.parent_id.is_(None))
    result = await db.execute(query.order_by(Collection.name))
    return result.scalars().all()


@router.get("/{collection_id}", response_model=CollectionWithAssetsResponse)
async def get_collection(
    collection_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(Collection)
        .where(Collection.id == collection_id)
        .options(selectinload(Collection.collection_assets))
    )
    collection = result.scalar_one_or_none()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Load associated assets
    asset_ids = [ca.asset_id for ca in collection.collection_assets]
    assets = []
    if asset_ids:
        asset_result = await db.execute(select(Asset).where(Asset.id.in_(asset_ids)))
        assets = asset_result.scalars().all()

    return CollectionWithAssetsResponse(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        collection_type=collection.collection_type.value
        if hasattr(collection.collection_type, "value")
        else collection.collection_type,
        parent_id=collection.parent_id,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
        assets=assets,
    )


@router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: UUID,
    body: CollectionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    result = await db.execute(
        select(Collection).where(Collection.id == collection_id)
    )
    collection = result.scalar_one_or_none()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    if body.name is not None:
        collection.name = body.name
    if body.description is not None:
        collection.description = body.description
    return collection


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_manager),
):
    result = await db.execute(
        select(Collection).where(Collection.id == collection_id)
    )
    collection = result.scalar_one_or_none()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    await db.delete(collection)


@router.post(
    "/{collection_id}/assets",
    status_code=status.HTTP_201_CREATED,
)
async def add_asset_to_collection(
    collection_id: UUID,
    asset_id: UUID = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # Verify both exist
    col_result = await db.execute(
        select(Collection).where(Collection.id == collection_id)
    )
    if not col_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Collection not found")

    asset_result = await db.execute(select(Asset).where(Asset.id == asset_id))
    if not asset_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Asset not found")

    ca = CollectionAsset(collection_id=collection_id, asset_id=asset_id)
    db.add(ca)
    await db.flush()
    return {"status": "added"}


@router.delete(
    "/{collection_id}/assets/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_asset_from_collection(
    collection_id: UUID,
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(CollectionAsset).where(
            CollectionAsset.collection_id == collection_id,
            CollectionAsset.asset_id == asset_id,
        )
    )
    ca = result.scalar_one_or_none()
    if not ca:
        raise HTTPException(status_code=404, detail="Asset not in collection")
    await db.delete(ca)
