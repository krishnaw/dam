"""Video transcoding and document preview Celery tasks."""

import os
import tempfile
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import Asset, Rendition, RenditionType
from app.services.storage import MinIOStorage
from app.tasks.celery_app import celery_app

sync_db_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
sync_engine = create_engine(sync_db_url, echo=False)
SyncSession = sessionmaker(sync_engine, expire_on_commit=False)


@celery_app.task(name="app.tasks.transcode.transcode_video", bind=True, max_retries=2)
def transcode_video(
    self, asset_id: str, codec: str = "libx264", resolution: str | None = None
):
    """Transcode video to target format/resolution."""
    from app.services.video import VideoService

    storage = MinIOStorage()
    storage.ensure_bucket()

    with SyncSession() as db:
        asset = db.get(Asset, uuid.UUID(asset_id))
        if not asset:
            return {"error": "Asset not found"}

        # Download original to temp file
        file_data = storage.download(asset.storage_path)
        ext = asset.original_filename.rsplit(".", 1)[-1] if "." in asset.original_filename else "mp4"

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, f"input.{ext}")
            output_path = os.path.join(tmpdir, "output.mp4")

            with open(input_path, "wb") as f:
                f.write(file_data)

            # Transcode
            VideoService.transcode(
                input_path, output_path, codec=codec, resolution=resolution
            )

            # Read transcoded file
            with open(output_path, "rb") as f:
                transcoded_data = f.read()

            # Parse resolution for rendition record
            width, height = None, None
            if resolution:
                parts = resolution.split("x")
                width, height = int(parts[0]), int(parts[1])

            # Upload to MinIO
            rendition_key = f"renditions/{asset_id}/web_{uuid.uuid4().hex}.mp4"
            storage.upload(
                rendition_key, transcoded_data, "video/mp4", len(transcoded_data)
            )

            # Create Rendition record
            rendition = Rendition(
                asset_id=asset.id,
                rendition_type=RenditionType.web,
                storage_path=rendition_key,
                width=width,
                height=height,
                file_format="mp4",
                file_size=len(transcoded_data),
            )
            db.add(rendition)
            db.commit()

    return {"status": "transcoded", "asset_id": asset_id}


@celery_app.task(
    name="app.tasks.transcode.generate_doc_preview", bind=True, max_retries=2
)
def generate_doc_preview(self, asset_id: str, max_pages: int = 10):
    """Generate preview images for document."""
    from app.services.document import DocumentService

    storage = MinIOStorage()
    storage.ensure_bucket()

    with SyncSession() as db:
        asset = db.get(Asset, uuid.UUID(asset_id))
        if not asset:
            return {"error": "Asset not found"}

        file_data = storage.download(asset.storage_path)

        # Generate preview images
        if asset.content_type == "application/pdf":
            previews = DocumentService.generate_pdf_previews(file_data, max_pages)
        else:
            previews = DocumentService.generate_office_previews(
                file_data, asset.original_filename, max_pages
            )

        # Upload each page and create Rendition records
        for i, preview_data in enumerate(previews):
            preview_key = f"renditions/{asset_id}/preview_page_{i + 1:03d}.jpg"
            storage.upload(preview_key, preview_data, "image/jpeg", len(preview_data))

            rendition = Rendition(
                asset_id=asset.id,
                rendition_type=RenditionType.preview,
                storage_path=preview_key,
                file_format="jpeg",
                file_size=len(preview_data),
            )
            db.add(rendition)

        db.commit()

    return {"status": "previews_generated", "asset_id": asset_id, "pages": len(previews)}
