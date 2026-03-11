"""Asset ingestion Celery task - uses synchronous DB session."""

import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models import Asset, AssetMetadata, AssetStatus, Rendition, RenditionType
from app.services.media import (
    compute_checksum,
    detect_content_type,
    extract_image_dimensions,
    generate_thumbnail,
)
from app.services.storage import MinIOStorage
from app.tasks.celery_app import celery_app

# Synchronous engine for Celery tasks
sync_db_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
sync_engine = create_engine(sync_db_url, echo=False)
SyncSession = sessionmaker(sync_engine, expire_on_commit=False)


@celery_app.task(name="app.tasks.ingest.process_asset_upload", bind=True, max_retries=3)
def process_asset_upload(self, asset_id: str) -> dict:
    """Process an uploaded asset: thumbnail, metadata, checksum, CLIP, OCR, search index."""
    storage = MinIOStorage()
    storage.ensure_bucket()

    with SyncSession() as db:
        asset = db.get(Asset, uuid.UUID(asset_id))
        if not asset:
            return {"error": "Asset not found"}

        # Download original from MinIO
        file_data = storage.download(asset.storage_path)

        # Compute checksum
        checksum = compute_checksum(file_data)
        asset.checksum_sha256 = checksum

        # Detect content type
        detected_type = detect_content_type(file_data)

        # Extract dimensions (for images)
        is_image = asset.content_type.startswith("image/")
        if is_image:
            dims = extract_image_dimensions(file_data)
            if dims:
                asset.width, asset.height = dims

            # Generate thumbnail
            try:
                thumb_data = generate_thumbnail(file_data, asset.content_type)
                thumb_path = f"thumbnails/{asset_id}.jpg"
                storage.upload(thumb_path, thumb_data, "image/jpeg", len(thumb_data))

                rendition = Rendition(
                    asset_id=asset.id,
                    rendition_type=RenditionType.thumbnail,
                    storage_path=thumb_path,
                    width=300,
                    height=300,
                    file_format="jpeg",
                    file_size=len(thumb_data),
                )
                db.add(rendition)
            except Exception:
                pass  # Thumbnail generation may fail for some formats

            # Generate CLIP embedding
            try:
                from app.services.ai import generate_clip_embedding

                embedding = generate_clip_embedding(file_data)
                if embedding:
                    asset.embedding = embedding
            except Exception:
                pass  # CLIP model may not be available

            # Run OCR
            try:
                from app.services.ai import extract_text_ocr

                ocr_text = extract_text_ocr(file_data)
                if ocr_text:
                    db.add(
                        AssetMetadata(
                            asset_id=asset.id,
                            key="ocr_text",
                            value=ocr_text,
                            source="auto",
                        )
                    )
            except Exception:
                pass  # OCR may not be available

        # Store metadata
        meta_entries = [
            AssetMetadata(
                asset_id=asset.id,
                key="content_type_detected",
                value=detected_type,
                source="auto",
            ),
            AssetMetadata(
                asset_id=asset.id,
                key="checksum_sha256",
                value=checksum,
                source="auto",
            ),
        ]
        if is_image and asset.width and asset.height:
            meta_entries.append(
                AssetMetadata(
                    asset_id=asset.id,
                    key="dimensions",
                    value=f"{asset.width}x{asset.height}",
                    source="auto",
                )
            )
        db.add_all(meta_entries)

        # Index in Meilisearch
        try:
            from app.services.search import MeilisearchService

            svc = MeilisearchService()
            svc.ensure_index()
            svc.index_asset(
                {
                    "id": str(asset.id),
                    "filename": asset.filename,
                    "original_filename": asset.original_filename,
                    "content_type": asset.content_type,
                    "file_size": asset.file_size,
                    "description": asset.description or "",
                    "status": "active",
                    "created_at": asset.created_at.isoformat(),
                }
            )
        except Exception:
            pass  # Meilisearch may not be available

        # Video processing: extract thumbnail and queue transcode
        is_video = asset.content_type.startswith("video/")
        if is_video:
            try:
                from app.services.video import VideoService

                import tempfile
                import os

                ext = asset.original_filename.rsplit(".", 1)[-1] if "." in asset.original_filename else "mp4"
                with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
                    tmp.write(file_data)
                    tmp_path = tmp.name

                try:
                    # Extract video info
                    info = VideoService.get_video_info(tmp_path)
                    asset.width = info.get("width")
                    asset.height = info.get("height")
                    asset.duration = info.get("duration")

                    meta_entries.append(
                        AssetMetadata(
                            asset_id=asset.id,
                            key="video_codec",
                            value=info.get("codec", "unknown"),
                            source="auto",
                        )
                    )

                    # Extract thumbnail at 1s
                    thumb_data = VideoService.extract_thumbnail(tmp_path, timestamp=1.0)
                    thumb_path = f"thumbnails/{asset_id}.jpg"
                    storage.upload(thumb_path, thumb_data, "image/jpeg", len(thumb_data))

                    rendition = Rendition(
                        asset_id=asset.id,
                        rendition_type=RenditionType.thumbnail,
                        storage_path=thumb_path,
                        file_format="jpeg",
                        file_size=len(thumb_data),
                    )
                    db.add(rendition)
                finally:
                    os.unlink(tmp_path)

                # Queue transcode task
                from app.tasks.transcode import transcode_video

                transcode_video.delay(asset_id)
            except Exception:
                pass

        # Document processing: queue preview generation
        is_document = (
            asset.content_type == "application/pdf"
            or asset.content_type.startswith("application/vnd.openxmlformats-officedocument")
            or asset.content_type.startswith("application/vnd.ms-")
            or asset.content_type == "application/msword"
        )
        if is_document:
            try:
                from app.tasks.transcode import generate_doc_preview

                generate_doc_preview.delay(asset_id)
            except Exception:
                pass

        # Audio processing: store duration metadata
        is_audio = asset.content_type.startswith("audio/")
        if is_audio:
            meta_entries.append(
                AssetMetadata(
                    asset_id=asset.id,
                    key="media_type",
                    value="audio",
                    source="auto",
                )
            )

        # Update status
        asset.status = AssetStatus.active
        db.commit()

    # Dispatch AI tagging task
    try:
        from app.tasks.ai_tag import auto_tag_asset

        auto_tag_asset.delay(asset_id)
    except Exception:
        pass  # Celery may not be available

    return {"status": "processed", "asset_id": asset_id}
