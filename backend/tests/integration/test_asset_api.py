"""Integration tests for asset API endpoints."""

import io
import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.models.asset import Asset, AssetStatus


@pytest.fixture
def _mock_storage():
    """Patch MinIOStorage used within the assets router."""
    mock = MagicMock()
    mock.upload = MagicMock(return_value="originals/test.jpg")
    mock.download = MagicMock(return_value=b"fake-file-data")
    mock.delete = MagicMock()
    mock.get_url = MagicMock(return_value="http://minio/dam/file.jpg?presigned=true")
    mock.ensure_bucket = MagicMock()

    with patch("app.api.assets.MinIOStorage", return_value=mock):
        yield mock


class TestUploadAsset:
    async def test_upload_asset(self, client, auth_headers, _mock_storage):
        file_content = b"fake image data"
        resp = await client.post(
            "/api/assets/upload",
            headers=auth_headers,
            files={"file": ("test-image.jpg", io.BytesIO(file_content), "image/jpeg")},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert data["original_filename"] == "test-image.jpg"
        assert data["mime_type"] == "image/jpeg"
        assert data["status"] == "processing"


class TestListAssets:
    async def test_list_assets(self, client, auth_headers, db_session, make_asset):
        # Add assets directly to the DB
        for _ in range(3):
            asset = make_asset()
            db_session.add(asset)
        await db_session.flush()

        resp = await client.get("/api/assets/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 3
        assert data["page"] == 1

    async def test_list_assets_pagination(self, client, auth_headers, db_session, make_asset):
        for _ in range(5):
            db_session.add(make_asset())
        await db_session.flush()

        resp = await client.get(
            "/api/assets/", headers=auth_headers, params={"page": 1, "page_size": 2}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["per_page"] == 2
        assert len(data["items"]) <= 2


class TestGetAsset:
    async def test_get_asset(self, client, auth_headers, db_session, make_asset):
        asset = make_asset()
        db_session.add(asset)
        await db_session.flush()

        resp = await client.get(f"/api/assets/{asset.id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(asset.id)
        assert data["original_filename"] == "test-image.jpg"
        assert data["mime_type"] == "image/jpeg"
        assert data["file_size"] == 1024000

    async def test_get_asset_not_found(self, client, auth_headers):
        random_id = uuid.uuid4()
        resp = await client.get(f"/api/assets/{random_id}", headers=auth_headers)
        assert resp.status_code == 404


class TestUpdateAsset:
    async def test_update_asset(self, client, auth_headers, db_session, make_asset):
        asset = make_asset()
        db_session.add(asset)
        await db_session.flush()

        resp = await client.put(
            f"/api/assets/{asset.id}",
            headers=auth_headers,
            json={"description": "Updated description"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["description"] == "Updated description"


class TestDeleteAsset:
    async def test_delete_asset_soft(self, client, auth_headers, db_session, make_asset):
        asset = make_asset()
        db_session.add(asset)
        await db_session.flush()

        resp = await client.delete(f"/api/assets/{asset.id}", headers=auth_headers)
        assert resp.status_code == 204

        # Soft delete should archive the asset
        get_resp = await client.get(f"/api/assets/{asset.id}", headers=auth_headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["status"] == "archived"


class TestAssetVersions:
    async def test_list_asset_versions(self, client, auth_headers, db_session, make_asset):
        asset = make_asset()
        db_session.add(asset)
        await db_session.flush()

        resp = await client.get(f"/api/assets/{asset.id}/versions", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestAssetMetadata:
    async def test_update_asset_metadata(
        self, client, auth_headers, db_session, make_asset
    ):
        asset = make_asset()
        db_session.add(asset)
        await db_session.flush()

        resp = await client.put(
            f"/api/assets/{asset.id}/metadata",
            headers=auth_headers,
            json=[
                {"key": "camera", "value": "Canon EOS R5", "source": "exif"},
                {"key": "lens", "value": "RF 24-70mm f/2.8", "source": "exif"},
            ],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        keys = {entry["key"] for entry in data}
        assert "camera" in keys
        assert "lens" in keys
