"""Unit tests for MinIO storage service."""

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from app.services.storage import MinIOStorage


@pytest.fixture
def storage():
    """Create MinIOStorage with a mocked Minio client."""
    with patch("app.services.storage.Minio") as mock_minio_cls:
        mock_client = MagicMock()
        mock_minio_cls.return_value = mock_client
        svc = MinIOStorage()
        svc._mock_client = mock_client  # expose for assertions
        yield svc


class TestMinIOStorage:
    def test_upload_calls_put_object(self, storage):
        result = storage.upload("path/to/file.jpg", b"data", "image/jpeg", 4)
        storage._mock_client.put_object.assert_called_once()
        call_args = storage._mock_client.put_object.call_args
        assert call_args[0][0] == storage.bucket  # bucket name
        assert call_args[0][1] == "path/to/file.jpg"  # object key
        assert call_args[1]["length"] == 4
        assert call_args[1]["content_type"] == "image/jpeg"
        assert result == "path/to/file.jpg"

    def test_download_calls_get_object(self, storage):
        mock_response = MagicMock()
        mock_response.read.return_value = b"file-content"
        storage._mock_client.get_object.return_value = mock_response

        data = storage.download("path/to/file.jpg")
        storage._mock_client.get_object.assert_called_once_with(
            storage.bucket, "path/to/file.jpg"
        )
        assert data == b"file-content"
        mock_response.close.assert_called_once()
        mock_response.release_conn.assert_called_once()

    def test_delete_calls_remove_object(self, storage):
        storage.delete("path/to/file.jpg")
        storage._mock_client.remove_object.assert_called_once_with(
            storage.bucket, "path/to/file.jpg"
        )

    def test_get_url_calls_presigned(self, storage):
        storage._mock_client.presigned_get_object.return_value = (
            "http://minio:9000/bucket/file.jpg?token=abc"
        )
        url = storage.get_url("path/to/file.jpg")
        storage._mock_client.presigned_get_object.assert_called_once()
        assert url == "http://minio:9000/bucket/file.jpg?token=abc"

    def test_get_url_custom_expiry(self, storage):
        from datetime import timedelta

        storage.get_url("file.jpg", expires=7200)
        call_args = storage._mock_client.presigned_get_object.call_args
        assert call_args[1]["expires"] == timedelta(seconds=7200)

    def test_ensure_bucket_creates_if_not_exists(self, storage):
        storage._mock_client.bucket_exists.return_value = False
        storage.ensure_bucket()
        storage._mock_client.bucket_exists.assert_called_once_with(storage.bucket)
        storage._mock_client.make_bucket.assert_called_once_with(storage.bucket)

    def test_ensure_bucket_skips_if_exists(self, storage):
        storage._mock_client.bucket_exists.return_value = True
        storage.ensure_bucket()
        storage._mock_client.bucket_exists.assert_called_once_with(storage.bucket)
        storage._mock_client.make_bucket.assert_not_called()
