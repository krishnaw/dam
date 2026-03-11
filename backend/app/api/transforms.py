from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.models import Asset, AssetStatus, Rendition, RenditionType
from app.services.auth import get_current_user
from app.services.media import transform_image
from app.services.storage import MinIOStorage

router = APIRouter(prefix="/api/assets", tags=["transforms"])


def _get_storage() -> MinIOStorage:
    storage = MinIOStorage()
    storage.ensure_bucket()
    return storage


@router.get("/{asset_id}/transform")
async def transform_asset(
    asset_id: UUID,
    w: int | None = Query(None, description="Target width"),
    h: int | None = Query(None, description="Target height"),
    fit: str = Query("cover", description="Fit mode: cover, contain, fill"),
    format: str | None = Query(None, alias="fmt", description="Output format: jpeg, png, webp"),
    quality: int = Query(85, ge=1, le=100),
    rotate: int | None = Query(None, description="Rotation degrees"),
    token: str | None = Query(None, description="JWT token for img tag auth"),
    db: AsyncSession = Depends(get_db),
):
    """On-the-fly image transformation."""
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if not asset.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Asset is not an image")

    if asset.status not in (AssetStatus.active, AssetStatus.processing):
        raise HTTPException(status_code=400, detail="Asset is not available")

    storage = _get_storage()
    try:
        file_data = storage.download(asset.storage_path)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to download asset")

    try:
        transformed_data, content_type = transform_image(
            file_data,
            width=w,
            height=h,
            fit=fit,
            format=format,
            quality=quality,
            rotate=rotate,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Image transformation failed")

    return Response(
        content=transformed_data,
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=86400",
            "Content-Length": str(len(transformed_data)),
        },
    )


@router.post("/{asset_id}/transcode", status_code=202)
async def queue_transcode(
    asset_id: UUID,
    codec: str = Query("libx264"),
    resolution: str | None = Query(None, description="e.g. 1920x1080, 1280x720"),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Queue video transcoding job."""
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if not asset.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Asset is not a video")

    if asset.status != AssetStatus.active:
        raise HTTPException(status_code=400, detail="Asset is not active")

    try:
        from app.tasks.transcode import transcode_video

        task = transcode_video.delay(str(asset.id), codec, resolution)
        return {"task_id": task.id, "status": "queued", "asset_id": str(asset.id)}
    except Exception:
        raise HTTPException(status_code=503, detail="Task queue unavailable")


@router.get("/{asset_id}/preview")
async def get_document_preview(
    asset_id: UUID,
    page: int = Query(1, ge=1),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get document preview (rendered page image)."""
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    is_document = (
        asset.content_type == "application/pdf"
        or asset.content_type.startswith(
            "application/vnd.openxmlformats-officedocument"
        )
        or asset.content_type.startswith("application/vnd.ms-")
        or asset.content_type == "application/msword"
    )
    if not is_document:
        raise HTTPException(status_code=400, detail="Asset is not a document")

    # Check if a pre-generated rendition exists for this page
    rendition_result = await db.execute(
        select(Rendition).where(
            Rendition.asset_id == asset_id,
            Rendition.rendition_type == RenditionType.preview,
        )
    )
    renditions = rendition_result.scalars().all()

    # Sort by storage_path to maintain page order
    renditions = sorted(renditions, key=lambda r: r.storage_path)

    if renditions and page <= len(renditions):
        storage = _get_storage()
        try:
            preview_data = storage.download(renditions[page - 1].storage_path)
            return Response(
                content=preview_data,
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=86400"},
            )
        except Exception:
            pass

    # Generate on-the-fly if no rendition exists
    storage = _get_storage()
    try:
        file_data = storage.download(asset.storage_path)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to download asset")

    from app.services.document import DocumentService

    if asset.content_type == "application/pdf":
        previews = DocumentService.generate_pdf_previews(file_data, max_pages=page)
    else:
        previews = DocumentService.generate_office_previews(
            file_data, asset.original_filename, max_pages=page
        )

    if not previews or page > len(previews):
        raise HTTPException(status_code=404, detail="Page not found")

    return Response(
        content=previews[page - 1],
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )
