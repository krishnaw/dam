"""AI tagging Celery task - uses synchronous DB session."""

import asyncio
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import Asset, AssetMetadata
from app.services.ai import LLMFallbackChain, _parse_tag_response
from app.tasks.celery_app import celery_app

sync_db_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
sync_engine = create_engine(sync_db_url, echo=False)
SyncSession = sessionmaker(sync_engine, expire_on_commit=False)


@celery_app.task(name="app.tasks.ai_tag.auto_tag_asset", bind=True, max_retries=3)
def auto_tag_asset(self, asset_id: str) -> dict:
    """Auto-tag an asset using LLM with categorized tags."""
    with SyncSession() as db:
        asset = db.get(Asset, uuid.UUID(asset_id))
        if not asset:
            return {"error": "Asset not found"}

        context = (
            f"Filename: {asset.original_filename}, "
            f"Type: {asset.content_type}, "
            f"Size: {asset.file_size} bytes"
        )
        if asset.description:
            context += f", Description: {asset.description}"

        # Include OCR text if available
        ocr_meta = (
            db.query(AssetMetadata)
            .filter_by(asset_id=asset.id, key="ocr_text")
            .first()
        )
        if ocr_meta and ocr_meta.value:
            context += f", OCR text: {ocr_meta.value[:500]}"

        llm = LLMFallbackChain()
        loop = asyncio.new_event_loop()
        tags = []
        try:
            # Generate description if missing
            if not asset.description:
                description = loop.run_until_complete(llm.generate_description(context))
                if description:
                    asset.description = description

            # Generate categorized tags
            tag_context = asset.description or context
            tag_prompt = (
                "Analyze this digital asset and generate 5-15 tags. "
                "Include tags from these categories: objects, scene, mood, colors, style. "
                "Return ONLY a JSON array of tag strings.\n\n"
                f"Asset: {tag_context}"
            )
            raw_tags = loop.run_until_complete(llm.generate(tag_prompt))
            tags = _parse_tag_response(raw_tags)

            for tag in tags:
                db.add(
                    AssetMetadata(
                        asset_id=asset.id,
                        key="tag",
                        value=str(tag).lower().strip(),
                        source="auto",
                    )
                )

            # Generate AI description and store as metadata
            ai_desc = loop.run_until_complete(
                llm.generate_description(tag_context)
            )
            if ai_desc:
                db.add(
                    AssetMetadata(
                        asset_id=asset.id,
                        key="ai_description",
                        value=ai_desc,
                        source="auto",
                    )
                )

            db.commit()
        finally:
            loop.close()

    return {"status": "tagged", "asset_id": asset_id, "tag_count": len(tags)}
