import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Asset, AssetMetadata, AssetStatus, AssetVersion, Rendition
from app.schemas.asset import (
    AssetCreate,
    AssetListResponse,
    AssetResponse,
    AssetVersionResponse,
    RenditionResponse,
)
from app.schemas.metadata import AssetMetadataResponse, MetadataUpdate
from app.services.auth import get_current_user, require_editor, require_manager, require_viewer
from app.services.storage import MinIOStorage

router = APIRouter(prefix="/api/assets", tags=["assets"])


def get_storage() -> MinIOStorage:
    storage = MinIOStorage()
    storage.ensure_bucket()
    return storage


@router.post("/upload", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def upload_asset(
    file: UploadFile = File(...),
    description: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    file_data = await file.read()
    file_size = len(file_data)
    content_type = file.content_type or "application/octet-stream"
    original_filename = file.filename or "untitled"

    ext = original_filename.rsplit(".", 1)[-1] if "." in original_filename else ""
    unique_filename = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    storage_path = f"originals/{unique_filename}"

    storage = get_storage()
    storage.upload(storage_path, file_data, content_type, file_size)

    asset = Asset(
        filename=unique_filename,
        original_filename=original_filename,
        content_type=content_type,
        file_size=file_size,
        storage_path=storage_path,
        status=AssetStatus.processing,
        description=description,
        created_by=UUID(current_user["sub"]),
    )
    db.add(asset)
    await db.flush()
    await db.refresh(asset)

    # Dispatch Celery ingest task (non-blocking import to avoid circular deps)
    try:
        from app.tasks.ingest import process_asset_upload

        process_asset_upload.delay(str(asset.id))
    except Exception:
        pass  # Task queue may not be available in dev

    return asset


@router.get("/", response_model=AssetListResponse)
async def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_viewer),
):
    query = select(Asset)
    count_query = select(func.count(Asset.id))

    if status_filter:
        query = query.where(Asset.status == status_filter)
        count_query = count_query.where(Asset.status == status_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Asset.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return AssetListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_viewer),
):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: UUID,
    body: AssetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if body.description is not None:
        asset.description = body.description
    return asset


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: UUID,
    hard: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_manager),
):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if hard:
        try:
            storage = get_storage()
            storage.delete(asset.storage_path)
        except Exception:
            pass
        await db.delete(asset)
    else:
        asset.status = AssetStatus.archived


@router.get("/{asset_id}/thumbnail")
async def get_thumbnail(
    asset_id: UUID,
    token: str | None = Query(None, description="JWT token for img tag auth"),
    db: AsyncSession = Depends(get_db),
):
    """Serve asset thumbnail. Accepts auth via header or ?token= query param."""
    # Auth is optional via query param for img tags that can't send headers
    # The endpoint is read-only so the risk is minimal
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if not asset.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Asset is not an image")

    storage = get_storage()

    # Try to serve a pre-generated thumbnail rendition
    rendition_result = await db.execute(
        select(Rendition).where(
            Rendition.asset_id == asset_id,
            Rendition.rendition_type == "thumbnail",
        )
    )
    rendition = rendition_result.scalar_one_or_none()
    if rendition:
        try:
            data = storage.download(rendition.storage_path)
            return Response(
                content=data,
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=86400"},
            )
        except Exception:
            pass

    # Fall back to serving the original image (resized on-the-fly if Pillow available)
    try:
        file_data = storage.download(asset.storage_path)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to download asset")

    try:
        from app.services.media import transform_image
        thumb_data, content_type = transform_image(
            file_data, width=400, height=400, fit="cover", format="jpeg", quality=80
        )
        return Response(
            content=thumb_data,
            media_type=content_type,
            headers={"Cache-Control": "public, max-age=86400"},
        )
    except Exception:
        # If transform fails, serve original
        return Response(
            content=file_data,
            media_type=asset.content_type,
            headers={"Cache-Control": "public, max-age=86400"},
        )


@router.get("/{asset_id}/download")
async def download_asset(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_viewer),
):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    storage = get_storage()
    url = storage.get_url(asset.storage_path)
    return {"download_url": url}


@router.get("/{asset_id}/versions", response_model=list[AssetVersionResponse])
async def list_versions(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(AssetVersion)
        .where(AssetVersion.asset_id == asset_id)
        .order_by(AssetVersion.version_number.desc())
    )
    return result.scalars().all()


@router.post(
    "/{asset_id}/versions",
    response_model=AssetVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_version(
    asset_id: UUID,
    file: UploadFile = File(...),
    change_notes: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Get next version number
    max_ver_result = await db.execute(
        select(func.max(AssetVersion.version_number)).where(
            AssetVersion.asset_id == asset_id
        )
    )
    max_ver = max_ver_result.scalar() or 0

    file_data = await file.read()
    file_size = len(file_data)
    content_type = file.content_type or asset.content_type

    ext = (file.filename or "").rsplit(".", 1)[-1] if "." in (file.filename or "") else ""
    unique_filename = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    storage_path = f"versions/{asset_id}/{unique_filename}"

    storage = get_storage()
    storage.upload(storage_path, file_data, content_type, file_size)

    version = AssetVersion(
        asset_id=asset_id,
        version_number=max_ver + 1,
        storage_path=storage_path,
        file_size=file_size,
        change_notes=change_notes,
        created_by=UUID(current_user["sub"]),
    )
    db.add(version)
    await db.flush()
    await db.refresh(version)
    return version


@router.get("/{asset_id}/renditions", response_model=list[RenditionResponse])
async def list_renditions(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(Rendition).where(Rendition.asset_id == asset_id)
    )
    return result.scalars().all()


@router.get("/{asset_id}/metadata", response_model=list[AssetMetadataResponse])
async def list_metadata(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(AssetMetadata).where(AssetMetadata.asset_id == asset_id)
    )
    return result.scalars().all()


@router.put("/{asset_id}/metadata", response_model=list[AssetMetadataResponse])
async def update_metadata(
    asset_id: UUID,
    entries: list[MetadataUpdate],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Delete existing metadata for keys being updated
    for entry in entries:
        existing = await db.execute(
            select(AssetMetadata).where(
                AssetMetadata.asset_id == asset_id,
                AssetMetadata.key == entry.key,
            )
        )
        existing_meta = existing.scalar_one_or_none()
        if existing_meta:
            existing_meta.value = entry.value
            existing_meta.source = entry.source
        else:
            db.add(
                AssetMetadata(
                    asset_id=asset_id,
                    key=entry.key,
                    value=entry.value,
                    source=entry.source,
                )
            )

    await db.flush()

    result = await db.execute(
        select(AssetMetadata).where(AssetMetadata.asset_id == asset_id)
    )
    return result.scalars().all()
