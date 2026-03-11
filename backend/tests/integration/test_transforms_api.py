"""Integration tests for transforms API endpoints."""

import uuid
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from PIL import Image

from app.models.asset import AssetStatus


@pytest.fixture
def fake_jpeg_bytes():
    """Create a minimal valid JPEG image."""
    img = Image.new("RGB", (800, 600), color="red")
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class TestTransformImageEndpoint:
    @pytest.mark.asyncio
    async def test_transform_resize(self, client, db_session, auth_headers, make_asset, fake_jpeg_bytes):
        asset = make_asset(content_type="image/jpeg", status=AssetStatus.active)
        db_session.add(asset)
        await db_session.flush()

        with patch("app.api.transforms._get_storage") as mock_storage_fn:
            mock_storage = MagicMock()
            mock_storage.download.return_value = fake_jpeg_bytes
            mock_storage_fn.return_value = mock_storage

            resp = await client.get(
                f"/api/assets/{asset.id}/transform?w=200&h=200&fit=cover",
                headers=auth_headers,
            )

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/jpeg"

        img = Image.open(BytesIO(resp.content))
        assert img.size == (200, 200)

    @pytest.mark.asyncio
    async def test_transform_format_conversion(self, client, db_session, auth_headers, make_asset, fake_jpeg_bytes):
        asset = make_asset(content_type="image/jpeg", status=AssetStatus.active)
        db_session.add(asset)
        await db_session.flush()

        with patch("app.api.transforms._get_storage") as mock_storage_fn:
            mock_storage = MagicMock()
            mock_storage.download.return_value = fake_jpeg_bytes
            mock_storage_fn.return_value = mock_storage

            resp = await client.get(
                f"/api/assets/{asset.id}/transform?fmt=png",
                headers=auth_headers,
            )

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"

    @pytest.mark.asyncio
    async def test_transform_rejects_non_image(self, client, db_session, auth_headers, make_asset):
        asset = make_asset(content_type="video/mp4", status=AssetStatus.active)
        db_session.add(asset)
        await db_session.flush()

        resp = await client.get(
            f"/api/assets/{asset.id}/transform?w=200",
            headers=auth_headers,
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_transform_404_for_missing_asset(self, client, auth_headers):
        fake_id = uuid.uuid4()
        resp = await client.get(
            f"/api/assets/{fake_id}/transform?w=200",
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestQueueTranscode:
    @pytest.mark.asyncio
    async def test_queue_transcode_video(self, client, db_session, auth_headers, make_asset):
        asset = make_asset(content_type="video/mp4", status=AssetStatus.active)
        db_session.add(asset)
        await db_session.flush()

        mock_task = MagicMock()
        mock_task.delay.return_value = MagicMock(id="task-123")
        mock_transcode_mod = MagicMock()
        mock_transcode_mod.transcode_video = mock_task

        with patch.dict("sys.modules", {"app.tasks.transcode": mock_transcode_mod}):
            resp = await client.post(
                f"/api/assets/{asset.id}/transcode",
                headers=auth_headers,
            )

        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "queued"
        assert data["task_id"] == "task-123"

    @pytest.mark.asyncio
    async def test_transcode_rejects_non_video(self, client, db_session, auth_headers, make_asset):
        asset = make_asset(content_type="image/jpeg", status=AssetStatus.active)
        db_session.add(asset)
        await db_session.flush()

        resp = await client.post(
            f"/api/assets/{asset.id}/transcode",
            headers=auth_headers,
        )
        assert resp.status_code == 400


class TestGetDocumentPreview:
    @pytest.mark.asyncio
    async def test_preview_pdf(self, client, db_session, auth_headers, make_asset):
        asset = make_asset(content_type="application/pdf", status=AssetStatus.active)
        db_session.add(asset)
        await db_session.flush()

        img = Image.new("RGB", (100, 100), color="white")
        buf = BytesIO()
        img.save(buf, format="JPEG")
        fake_preview = buf.getvalue()

        with patch("app.api.transforms._get_storage") as mock_storage_fn, \
             patch("app.services.document.DocumentService") as mock_doc:
            mock_storage = MagicMock()
            mock_storage.download.return_value = b"fake-pdf"
            mock_storage_fn.return_value = mock_storage
            mock_doc.generate_pdf_previews.return_value = [fake_preview]

            resp = await client.get(
                f"/api/assets/{asset.id}/preview?page=1",
                headers=auth_headers,
            )

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/jpeg"

    @pytest.mark.asyncio
    async def test_preview_rejects_non_document(self, client, db_session, auth_headers, make_asset):
        asset = make_asset(content_type="image/jpeg", status=AssetStatus.active)
        db_session.add(asset)
        await db_session.flush()

        resp = await client.get(
            f"/api/assets/{asset.id}/preview?page=1",
            headers=auth_headers,
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_preview_page_not_found(self, client, db_session, auth_headers, make_asset):
        asset = make_asset(content_type="application/pdf", status=AssetStatus.active)
        db_session.add(asset)
        await db_session.flush()

        with patch("app.api.transforms._get_storage") as mock_storage_fn, \
             patch("app.services.document.DocumentService") as mock_doc:
            mock_storage = MagicMock()
            mock_storage.download.return_value = b"fake-pdf"
            mock_storage_fn.return_value = mock_storage
            mock_doc.generate_pdf_previews.return_value = []

            resp = await client.get(
                f"/api/assets/{asset.id}/preview?page=5",
                headers=auth_headers,
            )

        assert resp.status_code == 404
